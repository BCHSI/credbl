library(glue)
library(bit64)
# COLORBLIND FRIENDLY COLOR PALETTES
# http://www.cookbook-r.com/Graphs/Colors_(ggplot2)/#a-colorblind-friendly-palette 
# The palette with grey:
cbPalette <- c("#999999", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7")
# The palette with black:
cbbPalette <- c("#000000", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7")


#' https://stackoverflow.com/questions/30057278/get-lhs-object-name-when-piping-with-dplyr
get_orig_name <- function(df){
  i <- 1
  while(!("chain_parts" %in% ls(envir=parent.frame(i))) && i < sys.nframe()) {
    i <- i+1
  }
  deparse(parent.frame(i)$lhs)
  # list(name = deparse(parent.frame(i)$lhs), output = df)
}


#' Copy a dbplyr object to a temporary table
#' table name is created dynamically from the name of 1st input variable
copy_to_temporary <- function(input_table, database, schema='home', name=NULL){
  if (is.null(name)){
    name <- deparse(substitute(input_table))
    if (name=='.'){
      # this means the table object is being piped
      name <- get_orig_name(input_table)
    }
  }
  
  tmp_table <- glue("{schema}.{name}")
  tmp_table <- paste(schema, name, sep='.')
  if (!grepl('^##', tmp_table)){
    tmp_table <- paste0('##', tmp_table)
  }
  print(tmp_table)
  try(  DBI::dbRemoveTable(database, tmp_table, fail_if_missing=F), silent=T)
  dplyr::copy_to(database,
                 input_table,
                 tmp_table,
                 overwrite=T)
}


#' https://stackoverflow.com/questions/41047900/calculate-median-on-pre-aggregated-data-having-means-and-counts-in-r-rstats
median_from_counts <- function(data, keys, histogram){
  keys <- deparse(substitute(keys))
  histogram <- deparse(substitute(histogram))
  data %>% with(median(rep.int(n_measurements, f)) )
}

##' function to count rows in a table of a database
nrow_ <- function(table_a){
  # extract database connection
  connection = table_a$src$con
  table_name = str_split(as.character(sql_render(table_a)), "FROM ")[[1]][2]
  sql_query <- glue('SELECT count(*) FROM {table_name}')
  print(sql_query)
  DBI::dbGetQuery(connection, sql_query)
}
#setMethod("nrow", signature("tbl_Microsoft SQL Server"),   nrow_)
#setMethod("nrow", signature("tbl_dbi"),   nrow_)

t_ <- function(db_table, n=3){
    db_table %>% head(n) %>% as_tibble() %>% t()
}

get_system_user <- function(){
  user <- Sys.getenv("USERNAME")
  if (length(user)==0){
    user <- str_split(Sys.getenv("HOME"),'/')[[1]] %>% tail(1)
  }
  user
}

#' request credentials or retrieve them from system's keyring
#' if reset=T -- clears the keyring
get_credentials_direct <- function(dbname,  uid=NULL, reset=F, domain=T){
  if (reset) keyring::key_delete(dbname, username = uid, keyring = NULL)

  uid <- keyring::key_list(dbname) %>%
    filter(!(username %in% c("username", "uid"))) %>%
    .[,2]  %>% tail(1)

  if (length(uid)==0 || is.na(uid) || str_length(uid)==0) {
    
    if (domain){
      title=paste("domain and username for '", dbname, "'")
      message="Please enter your UCSF DOMAIN\\username"
      default = paste0('SOM\\', get_system_user())
    } else {
      title=paste("username for '", dbname, "'")
      message="Please enter your username"
      default=get_system_user()
    }
    uid <- rstudioapi::showPrompt(title=title,
                                  message=message, default=default)
    print(uid)
    stopifnot(length(uid)>0)
    if (domain) stopifnot(grepl('\\\\', uid))
    pwd <- rstudioapi::askForPassword(glue("{dbname} password for {uid}"))
    keyring::key_set_with_value(service=dbname, username=uid, password=pwd)
  } else {
    #uid <- keyring::key_list(dbname) %>%
    #  filter(!(username %in% c("username", "uid"))) %>%
    # .[,2]  %>% tail(1)
    pwd <- keyring::key_get(dbname, uid)
  }
  return( list(uid=uid, pwd=pwd) )
}

#' finds Windows ODBC credentials assuming the REGISTRY_FILE exists
#' breaks if file is missing (to be caught upstream)
find_odbc_by_server <- function(server, 
                                REGISTRY_FILE = "Software\\ODBC\\ODBC.INI"){
  odbc_ini <-  readRegistry(REGISTRY_FILE, hive="HCU", maxdepth=2)

  for (entry in odbc_ini){
    if ((length(entry$Server)>0) && (entry$Server == server)){
      registered <- TRUE
      break
    }
  }
  registered 
}

get_credentials_windows <- function(server, reset=F,
                                    REGISTRY_FILE = "Software\\ODBC\\ODBC.INI"){
  registered <- F
  if (!reset){
    registered <- tryCatch(find_odbc_by_server(server, REGISTRY_FILE),
                           error=function(e){FALSE}
    )
  }
  if (!registered){
    message = glue("create an entry in ODBC Data Source Administrator for server
                   {server}
                   =============================
                   You now will see the window where you'll need to press 'Add...' 
                   in the first (User DSN) tab. Select 'SQL Server' Driver")
    print(message)
    rstudioapi::showDialog(title="Reminder", message=message)
    system('c:\\Windows\\SysWOW64\\odbcad32.exe')
    return(list(uid=NULL, pwd=NULL))
  }
}

get_credentials <- function(server=NULL, reset=F, urlencode=F, forcekeyring=F, domain=T){
  print(glue("retrieving credentials for '{server}'"))
  if ((Sys.info()['sysname'] == 'Windows')&&!forcekeyring){
    credentials <- get_credentials_windows(server, reset=reset)
  } else {
    credentials <- get_credentials_direct(server, reset=reset, domain=domain)
  }
  if (urlencode){
    credentials$pwd = URLencode(credentials$pwd, reserved = TRUE)
  }
  credentials
}

get_mssql_driver <- function(dbconfig=list()){
  if (Sys.info()['sysname'] == 'Windows'){
    dbconfig$driver <- "SQL Server"
  } else {
    dbconfig$driver <- "FreeTDS"
    dbconfig$TDS_Version <- "7.3"
  }
  dbconfig
}

#' function to clean up mongoDB JSON to standard JSON and perform `glue` replacements with double braces
mj <- function(txt, replace=T,  .open = '{{', .close='}}'){
	  if (replace){
		       txt <- glue::glue(txt, .open = .open, .close=.close, .envir = parent.frame())
  }
  # quote dollar-sign variables
  txt <- gsub( '(?<!")(\\$[a-zA-Z_][a-zA-Z\\d_]+)', '"\\1"', txt, perl=TRUE)
    # remove trailing commas
    gsub( ',[ ]*(}|\\])', '\\1', txt)
}

#' translate a date into mongo numberLong query
date_to_mongo <- function(datestring, format="%Y-%m-%d"){
  startd <- datestring %>% strptime(format=format) %>% as.POSIXct() %>% 
    as.integer() %>% as.integer64() * 1000
  paste0('{ "$date" : { "$numberLong" : "', startd, '" } }')
}
