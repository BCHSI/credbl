library(magrittr)
library(glue)
library(bit64)
library(crayon)
library(stringr)

#' read current user name
get_system_user <- function(){
  user <- Sys.getenv("USERNAME")
  if (length(user)==0){
    user <- stringr::str_split(Sys.getenv("HOME"),'/')[[1]] %>% tail(1)
  }
  user
}

#' request credentials or retrieve them from system's keyring
#' if reset=T -- clears the keyring
get_credentials_direct <- function(dbname,  uid=NULL, reset=F, domain=T){

  uid <- keyring::key_list(dbname) %>%
    subset(!(username %in% c("username", "uid"))) %>%
    .[,2]  %>% tail(1)

    if (length(uid)>0 & reset) keyring::key_delete(dbname, username = uid, keyring = NULL)


  if (length(uid)==0 || is.na(uid) || stringr::str_length(uid)==0) {
    
    if (domain){
      title=paste("domain and username for '", dbname, "'")
      message="Please enter your DOMAIN\\username"
      default = paste0('SOM\\', get_system_user())
    } else {
      title=paste("username for '", dbname, "'")
      message="Please enter your username"
      default=get_system_user()
    }
    uid <- NULL
    while (is.null(uid)){
        uid <- rstudioapi::showPrompt(title=title,
                                      message=message, default=default)
        print(uid)
        stopifnot(length(uid)>0)
        if (domain) if(!grepl('\\\\', uid)){
            sure <- rstudioapi::showQuestion("No domain specified!", "are you sure your login has no DOMAIN\\ prefix?")
            if (!sure) {uid <- NULL}
        }
    }
    pwd <- rstudioapi::askForPassword(glue::glue("{dbname} password for {uid}"))
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

#' fetch / register credentials in the ODBC Data Source Administrator
get_credentials_windows <- function(server, reset=F,
                                    REGISTRY_FILE = "Software\\ODBC\\ODBC.INI"){
  registered <- F
  if (!reset){
    registered <- tryCatch(find_odbc_by_server(server, REGISTRY_FILE),
                           error=function(e){FALSE}
    )
  }
  if (!registered){
    highlight <- function(x) red(bold(x))
    message = glue::glue("create an entry in ODBC Data Source Administrator for server
                   {highlight(server)}
               
               Press '{highlight(\"Add...\")}'  in the first (User DSN) tab.
               Select '{highlight(\"SQL Server\")}' Driver
               {highlight(\"Name\")}          : short name describing the database (up to your imagination)
               {highlight(\"Description\")}  : you may leave it blank
               {highlight(\"Server\")}        : {highlight(server)}
               ")
    print(message)

    #sep <- paste0(rep("=", nchar(server)), collapse = '')
    highlight <- function(x) paste0("<b>", x, "</b>")

    message = glue::glue("create an entry in ODBC Data Source Administrator for server
                {highlight(server)}. See R console output for guidance.")
    rstudioapi::showDialog(title="Reminder", message=message)

    system('c:\\Windows\\SysWOW64\\odbcad32.exe')
    return(list(uid=NULL, pwd=NULL))
  }
}

#' retrieves or requests and stores credentials as necessary for ODBC connection
#' 
#' On Mac and Unix, credentials are stored in keyring 
#' (can be forced on Windows with forcekeyring=F)
#'
#' On Windows, ODBC Data Source Administrator is called 
#' (no credentials are explicitly retrieved -- list with NULL entries is returned
#' @export
#' @param server   server name (or any other identifier string that identifies username--password pair
#' @param reset    whether to reset credentials should they be already recorded in the registry
#' @param urlencode   URL-encode the password
#' @param forcekeyring   force keyring credential storage on Windows (on Mac and Unix keyring is used by default)
#' @param domain    require username to have a domain prefix ("domain\\username")
#' @return list(uid="myusername", pwd="password") # on Mac / Unix and list(uid=NULL, pwd=NULL) # on Windows
get_credentials <- function(server=NULL, reset=F, urlencode=F, forcekeyring=F, domain=T){
  print(glue::glue("retrieving credentials for '{server}'"))
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

#' retrieves default driver 
#'
#' retrieves default driver 
#' (Mac / Unix: FreeTDS, Windows: SQL Server)
#' @param dbconfig    configuration list (optional)
#' @return dbconfig    configuration list with driver name appended: list(driver="drivername", ...)
#' @examples
#' dbconfig <- read_yaml("database_info.yaml")
#' dbconfig <- get_mssql_driver(dbconfig)
#' credentials <- get_credentials(dbconfig$server)
#'
#' connection <- DBI::dbConnect(
#'     odbc(),
#'     driver=dbconfig$driver,
#'     server=dbconfig$server,
#'     port=dbconfig$port,
#'     uid=credentials$uid,
#'     pwd=credentials$pwd,
#'     database='mydatabase'
#'     )
#' @export
get_mssql_driver <- function(dbconfig=list()){
  if (Sys.info()['sysname'] == 'Windows'){
    dbconfig$driver <- "SQL Server"
  } else {
    dbconfig$driver <- "FreeTDS"
    # dbconfig$TDS_Version <- "7.3"
  }
  dbconfig
}


#' get a URI for mongodb connection given a config file and credentials stored in keyring
get_mongodb_uri <- function(configfile, reset=F){
  options(warn=-1)
  dbconfig <- read_yaml(configfile)
  options(warn=0)
  credentials <- get_credentials(dbconfig$server, urlencode=T, 
                                 forcekeyring=T, domain=F, reset=reset)
  
  mongo_uri = glue::glue("mongodb://{uid}:{pwd}@{server}:{port}/{db}?authSource={authSource}&authMechanism={authMechanism}", 
                   .envir = c(dbconfig, credentials))
  return(mongo_uri)
}

#' query clean-up and substitution for mongoDB
#'
#' cleans up mongoDB JSON to standard JSON and
#' perform `glue` replacements with double braces
#' @examples
#' # enclose variables that need to be substituted with double curvy braces, e.g.
#' term <- "tree"
#' mj('{$search: "{{term}}"')
#' # {"$search": "tree"}
#' @export

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
#' @examples
#' date_to_mongo('2020-03-18')
#' # { "$date" : { "$numberLong" : "1584514800000" } }
#' @export
date_to_mongo <- function(datestring, format="%Y-%m-%d"){
  startd <- datestring %>% strptime(format=format) %>% as.POSIXct() %>% 
    as.integer() %>% as.integer64() * 1000
  paste0('{ "$date" : { "$numberLong" : "', startd, '" } }')
}
