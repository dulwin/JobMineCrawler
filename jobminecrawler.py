import urllib, urllib2, cookielib
from bs4 import BeautifulSoup
from datetime import datetime;
import os
import smtplib
from email.mime.text import MIMEText

class Job:
    def __init__( self, title, company, status ):
        self.title = title
        self.company = company
        self.status = status

    # String representation of object
    def __str__( self ):
        return self.title + ' @ ' + self.company + ' - ' + self.status

    def __eq__( self, other ):
        return self.title == other.title or self.company == other.company or self.status == other.status

userid = ''     # Nexus/WatIam ID
pwd = ''        # Nexus Password
email = ''      # Gmail Address
email_pwd = ''  # Gmail Password

# Login to JobMine, navigate to applications list
def login ( userid, pwd ):
    cookies = cookielib.CookieJar( )

    # Browser
    browser = urllib2.build_opener( urllib2.HTTPCookieProcessor( cookies ) )

    # Login Data
    data = urllib.urlencode( {'userid' : userid, 'pwd' : pwd } )

    # Login to JobMine
    browser.open( 'https://jobmine.ccol.uwaterloo.ca/psp/SS/EMPLOYEE/WORK/', data )

    # Navigate to Applications Page
    response = browser.open( 'https://jobmine.ccol.uwaterloo.ca/psc/SS/EMPLOYEE/' +
        'WORK/c/UW_CO_STUDENTS.UW_CO_APP_SUMMARY.GBL?pslnkid=UW_CO_APP_SUMMARY_' +
        'LINK&FolderPath=PORTAL_ROOT_OBJECT.UW_CO_APP_SUMMARY_LINK&IsFolder=' +
        'false&IgnoreParamTempl=FolderPath%2cIsFolders' )

    # Parse page
    page = BeautifulSoup( response.read( ) )

    # Logout of JobMine
    browser.open( 'https://jobmine.ccol.uwaterloo.ca/psp/SS/EMPLOYEE/WORK/?cmd=logout' )

    # First Login to JobMine
    if not os.path.isfile( '.list' ):
        write_to_file( generate_list ( page ), '.list' )
        log ( str( datetime.now( ) ) + ' : First run' )

    return page

# Write file with job list for future comparisons
def write_to_file( list, filename ):
    f = open ( filename, 'w' )

    for item in list:
        f.write( item.title + '::' + item.company + '::' + item.status + '\n' )

    f.close( )

# Create list of previously generated jobs to compare to; read from file
def read_file( filename ):
    job_list = []

    f = open ( filename, 'r' )

    # Create job list from files
    for line in f:
        line = line.strip( '\n' ).split( '::' )
        job_list.append( Job( line[0], line[1], line[2] ) )

    f.close( );

    return job_list

# Generate list of jobs provided Applications page
def generate_list ( soup ):
    t_list = [] # Temporary lsit
    x = 0       # Element counter

    while True:
        # Fetch job title, job company, and job status from page data
        title = soup.find ( attrs={ 'id' : 'UW_CO_JB_TITLE2$%d' % x } )

        # If can't find any more job titles, break out of process
        if not title:
            break

        companies = soup.find( attrs={ 'id' : 'UW_CO_JOBINFOVW_UW_CO_PARENT_NAME$27$$%d' % x } )

        stats = soup.find( attrs={ 'id' : 'UW_CO_APPSTATVW_UW_CO_APPL_STATUS$32$$%d' % x } )

        # Write list of jobs
        t_list.append( Job(
            str(title)[str(title).find('>')+1:].strip( '[]' ).replace( '</a>', '' ),

            str(companies).strip( '[]' )
                .replace( '<span class="PSEDITBOX_DISPONLY" id="UW_CO_JOBINFOVW_UW_CO_PARENT_NAME$27$$%d">' % x , '' )
                .replace( '</span>', '' ),

            str( stats ).strip( '[]' )
                .replace( '<span class="PSDROPDOWNLIST_DISPONLY" id="UW_CO_APPSTATVW_UW_CO_APPL_STATUS$32$$%d">' % x , '' )
                .replace( '</span>', '' ) ) )

        # Increase element counter
        x += 1

    return t_list

# Compare list of filed jobs and JobMine jobs
def compare ( mine, file ):
    rewrite = False

    # If file list is shorter than JobMine list, rewrite is necessary
    if len( file ) != len( mine ):
        rewrite = True

    # Compare objects to find differences
    for f in file:
        for m in mine:
            if ( f.title == m.title and f.company == m.company ):
                # If status' different send email, update local list
                if ( f.status != m.status ):
                    send_email( m )
                    rewrite = True

                break

    return rewrite

def send_email ( job ):
    # Create a text/plain message
    msg = MIMEText( 'Job status has changed: \n' +
        '         - %s \n' % str( job ) +
        'Please check JobMine. \n\n - JobMineCrawler' )

    msg['Subject'] = 'Job Status Changed!'
    msg['From'] = email
    msg['To'] = email

    # Send email via gmail account
    s = smtplib.SMTP( 'smtp.gmail.com:587' )
    s.ehlo( )
    s.starttls( )
    s.login( email, email_pwd )
    s.sendmail( email, email, msg.as_string( ) )

    s.quit( )

# Log activity
def log ( msg ):
    with open( '.log', 'a' ) as f:
        f.write( msg + '\n' )

# Main Activity ----------------------------------------------------------------
time = datetime.now( );
try:
    soup = login( userid, pwd )                 # Log in to JobMine

    mine_list = generate_list( soup )           # Generate List of JobMine Jobs
    file_list = read_file( '.list' )            # Generate List of Jobs on file

     # If changes found, update list file
    changes_found = compare ( mine_list, file_list )
    if ( changes_found ):
        write_to_file( mine_list, '.list' )

    log ( str( time ) + ' : Script completed, changes found: ' + str( changes_found ) )
except Exception:
    log( str( time ) + ' : Something went wrong, script could not execute.' )
