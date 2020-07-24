#' credbl: Database Credential Management
#'
#' @section credbl functions:
#'
#' \itemize{
#' \item \code{\link{get_credentials}}  -- retrieve credentials 
#' \item \code{\link{get_mssql_driver}} -- retrieve driver
#' \item \code{\link{mj}}               -- format mongodb query 
#' \item \code{\link{date_to_mongo}}    -- convert date to mongodb format
#' }
#'
#' @examples
#' # connecting to a Microsoft SQL database with the ODBC driver
#'
#' # read server settings
#' dbconfig <- read_yaml("database_info.yaml")
#' # get driver
#' dbconfig <- get_mssql_driver(dbconfig)
#' # get credentials
#' credentials <- get_credentials(dbconfig$server)
#' 
#' connection <- DBI::dbConnect(
#'     odbc(),
#'     driver=dbconfig$driver,
#'     server=dbconfig$server,
#'     port=dbconfig$port,
#'     uid=credentials$uid,
#'     pwd=credentials$pwd,
#'     # database='mydatabase'
#'     )
#' @docType package
#' @name credbl
NULL
