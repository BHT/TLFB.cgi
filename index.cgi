#!/usr/bin/perl

#-------------------------------------------------------------------
# ONLINE Timeline Followback (TLFB)
#
# You may copy this software, and use it however you see fit.
# No guarantee or warranty of any kind is provided.
# Note that you will need to make a few modifications to the code to
#   customize for your setup.  
#  * setup your database (schema available at URL below)
#  * add your database name, username, and password to $dbh
#  * make sure permissions are set appropriately for this script and the db
# You should be good to go!  
#
# Joel Grow 
# http://depts.washington.edu/abrc/tlfb/
#-------------------------------------------------------------------

use strict;
use CGI;
use CGI::Carp qw(fatalsToBrowser);
use DBI;
use Date::Manip;


#-------------------------------------------------------------------
# Fill this in with your database name, username, and password
#-------------------------------------------------------------------
my $user 	= "uvabht_tlfb_user";
my $pw 		= "tlfb12345";
my $database 	= "uvabht_tlfb";
my $hostname 	= "mysql.uvabht.dreamhosters.com";
my $port 	= "3306";
my $dsn 	= "DBI:mysql:database=$database;host=$hostname;port=$port";

my $dbh = DBI->connect($dsn, $user, $pw)
          or die "Can't connect to db:" . DBI::errstr;


my $homepage = 'http://tlfb.dreamhosters.com/';

my $q = CGI->new;

#NOTE:
# this can't go above 364.
# 1 gets added to this number, for the total numbers of days displayed.
my $DAYS_TO_DISPLAY = 99;

# constants
my $DATE_FORM_MM   = 'a_';
my $DATE_FORM_DD   = 'b_';
my $DRINKS_FORM    = 'd_';
my $HOURS_FORM     = 'e_';
my $JOINTS_FORM    = 'f_';

# actions
my $DEFAULT_ACTION       = 'g_';
my $DISPLAY_INSTRUCTIONS = 'h_';
my $DISPLAY_MARKER_PAGE  = 'i_';
my $DISPLAY_CALENDAR     = 'j_';
my $PROCESS_ADD_MARKER   = 'l_';
my $PROCESS_CALENDAR     = 'm_';


my %months = (1 => 'January',
              2 => 'February',
              3 => 'March',
              4 => 'April',
              5 => 'May',
              6 => 'June',
              7 => 'July',
              8 => 'August', 
              9 => 'September',
              10 => 'October',
              11 => 'November',
              12 => 'December',
        );

my $SELF = $q->url('relative => 1');

my %dispatch = (
        $DEFAULT_ACTION       => \&page_one,
        $DISPLAY_INSTRUCTIONS => \&display_instructions,
        $DISPLAY_MARKER_PAGE  => \&display_marker_page,
        $PROCESS_ADD_MARKER   => \&process_add_marker,
        $DISPLAY_CALENDAR     => \&display_calendar,
        $PROCESS_CALENDAR     => \&process_calendar,
        );

my $action = $q->param('action');
my $subref = $dispatch{$action} || $dispatch{$DEFAULT_ACTION};

print_header();

$subref->();

print_footer();

exit;


sub process_add_marker {
    my $participant_id = $q->param('participant_id');

    my $insert_sql = <<End_of_SQL;
INSERT INTO marker_days 
(participant_id, date, description)
VALUES (?, ?, ?)
End_of_SQL

    my $sth = $dbh->prepare($insert_sql)
        or die "Can't prepare: " . $dbh->errstr;

    my $markers_added = 0;
    foreach my $i (1..10) { 
        my $description = $q->param("description_$i");
        my $mm   = $q->param("${DATE_FORM_MM}_$i");
        my $dd   = $q->param("${DATE_FORM_DD}_$i");

        next unless ($mm and $dd and $description);

        my $date = make_date({ mm => $mm, dd => $dd });

        $sth->execute($participant_id, $date, $description)
            or die "Can't execute: " . $sth->errstr;

        $markers_added++;
    }

    $dispatch{$DISPLAY_CALENDAR}->("$markers_added markers added");
}


sub display_calendar {
    my $msg = shift;

#
# these 2 set the time boundaries
# start_date: ($DAYS_TO_DISPLAY days ago) - stop_date
#
# current_day: holds the current marker day
# 
# previous month/year is the referer month/year
#

    my $participant_id = $q->param('participant_id');

    my $select_sql = <<End_of_SQL;
SELECT *
FROM   marker_days
WHERE  participant_id=?
End_of_SQL

    my $sth = $dbh->prepare($select_sql)
        or die "Couldn't prepare: " . $dbh->errstr;

    $sth->execute($participant_id) or die "Couldn't execute: " . $sth->errstr;

    # build %marker_days hash
    my %marker_days;
    while (my $r_row = $sth->fetchrow_hashref) {
        my $date        = $r_row->{date};  # MM/DD, no 0's
        my $description = $r_row->{description};

        $marker_days{$date} = $description;
    }

    my $prevmonthsubmit        = $q->param('prevmonthsubmit');
    my $nextmonthsubmit        = $q->param('nextmonthsubmit');
    my $finalsubmit            = $q->param('finalsubmit');
    my $previous_month         = $q->param('previous_month');
    my $previous_year          = $q->param('previous_year');

    my $stop_date   = UnixDate('today', "%Y%m%d");
    my $start_date  = UnixDate(
                        DateCalc($stop_date, "-$DAYS_TO_DISPLAY days"),
                        "%Y%m%d"
                      );
    my ($stop_yyyy, $stop_mm) = ($stop_date =~ /^(\d{4})(\d\d)/);

    my $current_day;
    if ($finalsubmit) {
        $dispatch{$PROCESS_CALENDAR}->($participant_id, $start_date, $stop_date);
        return;
    } elsif ($prevmonthsubmit) {
        $current_day = 
            UnixDate(
                    DateCalc("$previous_year/$previous_month/01", "-1 month"),
                    "%Y%m%d"
                    );
    } elsif ($nextmonthsubmit) {
        $current_day = 
            UnixDate(
                    DateCalc("$previous_year/$previous_month/01", "+1 month"),
                    "%Y%m%d"
                    );
    } else {
        $current_day = "$stop_yyyy${stop_mm}01";
    }

    my ($current_yyyy, $current_mm, $current_dd) = 
        $current_day =~ /^(\d{4})(\d{2})(\d{2})/;

    # returns 1 (Monday) to 7 (Sunday)
    my $first_day_of_month = UnixDate("$current_yyyy/$current_mm/01", "%w");
    my $days_in_month      = Date_DaysInMonth($current_mm, $current_yyyy);
    my $month_string       = UnixDate("$current_yyyy/$current_mm/$current_dd", "%B");


    print qq{<font color="red">$msg</font><br /><br />} if ($msg);

    print_instructions();

    print qq{
<div align="center">
  <center>
  <form action="$SELF" method="POST">
<table border="1" width="675" cellspacing="0" bgcolor="#FFFFFF" bordercolor="#808080" style="border-collapse: collapse">
     <tr>
      <td width="675" colspan="7" height="44">
        <p align="center">&nbsp;<br /><b><font face="Helvetica" size="5">$month_string $current_yyyy</font></b><br>
        <font size="2">&nbsp;</font>
      </p>
     </td>
    </tr>
    <tr>
      <td width="94" height="17">
        <p align="center"><strong><font size="2" face="Helvetica">Sunday</font></strong></td>

      <td width="94" height="17">
        <p align="center"><font size="2" face="Helvetica"><strong>Monday</strong></font></td>
      <td width="94" height="17">
        <p align="center"><font size="2" face="Helvetica"><strong>Tuesday</strong></font></td>
      <td width="94" height="17">
        <p align="center"><font size="2" face="Helvetica"><strong>Wednesday</strong></font></td>
      <td width="94" height="17">

        <p align="center"><font size="2" face="Helvetica"><strong>Thursday</strong></font></td>
      <td width="95" height="17">
        <p align="center"><font size="2" face="Helvetica"><strong>Friday</strong></font></td>
      <td width="95" height="17">
        <p align="center"><font size="2" face="Helvetica"><strong>Saturday</strong></font></td>
    </tr>
    };

    # find first day of the month
    print '<tr>';

    my $row_cell_count = 0;
    for my $dow (7, 1..6) {
        if ($first_day_of_month == $dow) {
            last;

        } else {
            $row_cell_count++;
            print qq{
  <td class="day other_month" width="94" height="107" align="left" valign="top">
   <font size="1">&nbsp;</font><font size="2"><b>&nbsp;</b></font></td>
            };
        }
    }

    for my $dom (1..$days_in_month) {
        if ($row_cell_count == 7) {
            print '</tr><tr>';
            $row_cell_count = 1;
        } else {
            $row_cell_count++;
        }

        my $comparison_date = sprintf("%d%02d%02d",$current_yyyy, $current_mm, $dom);
        if ($comparison_date >= $start_date and
            $comparison_date <= $stop_date) {

            my $comparison_mmdd = sprintf("%d/%d", $current_mm, $dom);
            my $marker_description = $marker_days{$comparison_mmdd};

            my ($marker_html, $class_text);
            if ($marker_description) {
                $marker_html = 
                   qq{<font color="red">$marker_description</font><br /><br />};
                $class_text = qq{class="day marker"};
            }

            print qq{
                    <td $class_text width="94" height="107" align="left" valign="top">
                     <font size="1">&nbsp;</font>
                     <b><font size="2">$dom</font></b>
                     <br /><br />$marker_html
            };

            # table cell
            print '<font face="Helvetica" size="2">Drinks: ', 
                  $q->textfield(-name => "${DRINKS_FORM}_$comparison_date",
                          -size => 2),

                  '<br />Joints: ',
                  $q->textfield(-name => "${JOINTS_FORM}_$comparison_date",
                          -size => 2),

                  '</font>';
          

            print ' </td>';

        } else {
            print qq{
     <td class="day noform" width="94" height="107" align="left" valign="top">
       <font size="1">&nbsp;</font>
       <b><font size="2">$dom</font></b>
     </td>
            };
        }
    }

    for my $eom_filler ($row_cell_count..6) {
        print qq{
  <td class="day other_month" width="94" height="107" align="left" valign="top">
   <font size="1">&nbsp;</font><font size="2"><b>&nbsp;</b></font>
   </td>
        };
    }

    print qq{
 </tr>
 <tr bgcolor="#9EA4A6" align="center"><td colspan="7">
 <input type="hidden" name="previous_month" value="$current_mm">
 <input type="hidden" name="previous_year" value="$current_yyyy">
 <input type="hidden" name="participant_id" value="$participant_id">
 <input type="hidden" name="action" value="$DISPLAY_CALENDAR">
    };

    my $next_month = UnixDate(
                        DateCalc($current_day, "+1 month"),
                        "%Y%m01"
            );

    if ($start_date < $current_day) {
        print 
        '<input type="submit" name="prevmonthsubmit" value="Previous Month">';
    } else {
        print '<input type="submit" name="finalsubmit" value="Calendar Complete">';
    }

    if ($stop_date > $next_month) {
        print '<input type="submit" name="nextmonthsubmit" value="Next Month">';
    } 

    foreach my $drink_form_var (grep { /${DRINKS_FORM}_/ } $q->param) {
        my $drink_val = $q->param($drink_form_var);
        print qq{<input type="hidden" name="$drink_form_var" value="$drink_val">\n};
    }
    foreach my $joints_var (grep { /${JOINTS_FORM}_/ } $q->param) {
        my $joints_val = $q->param($joints_var);
        print qq{<input type="hidden" name="$joints_var" value="$joints_val">\n};
    }
    foreach my $hours_var (grep { /${HOURS_FORM}_/ } $q->param) {
        my $hours_val = $q->param($hours_var);
        print qq{<input type="hidden" name="$hours_var" value="$hours_val">\n};
    }

    print '</form></td></tr></table>';

}


sub display_instructions {
    my $participant_id = $q->param('participant_id');
    my $sessionid     = $q->param('sessionid');

    if (!$participant_id) {
        $dispatch{$DEFAULT_ACTION}->();
        return;
    }

    print qq{
<div class="titlebox">
 <p align="center"><font size="2" face="Helvetica">INSTRUCTIONS FOR FILLING OUT THE TIMELINE USE CALENDAR
</div>

To help us evaluate your alcohol use, we need to get an idea of what your use was like in the past weeks. To do this, we would like you to fill out the following calendar.<br><br>Don't worry!! 

<br />
<ul>

<li>Filling out the calendar is not hard at all!</li>
<li>Try to be as accurate as possible.</li>
<li>We recognize you won't have perfect recall. That's totally  OKAY.</li>
</ul>

<p align="center"><strong>WHAT TO FILL IN</strong></p>
<ul>
<li>The idea is that for <strong>each day</strong> on the calendar we want you to indicate whether you "drank or "did not drink" alcohol.</li>
<li>On days when you <storng>did not drink alcohol</strong>, you should enter a "0" in the box.</li>
<li >On days when you <strong>did drink alcohol</strong>, you should put <strong>the number of drinks you had</strong> in the box.</li>
<br />
</ul>

<p align="center"><strong>YOUR BEST ESTIMATE</strong></p>
<ul>
<li>If you are not sure whether you had a drink on a Thursday or Friday of a certain week, <strong>give it your best guess!</strong></li>
</ul>
<strong>It's important that something is written for <u>every</u> day, even if it is a "0".</strong><br><br>
<p align="center"><strong>HELPFUL HINTS</strong></p>
<ul>
<li>Holidays such as Thanksgiving and Christmas are marked on the calendar to help you better recall your alcohol use. Also, think about whether you had a drink on personal holidays and events such as birthdays, vacations, or parties.</li>
<li>If you have <strong>regular alcohol use patterns</strong> you can use these to help you recall your use. For example, you may have weekend/weekday changes in your alcohol use depending on where you are or whom you are with.</li> 
</ul>
On the next page you'll fill in marker days.
<br />
<br />
<form action="$SELF" method="POST">
<input type="hidden" name="action" value="$DISPLAY_MARKER_PAGE">
<input type="hidden" name="participant_id" value="$participant_id">
<input type="submit" value="Next">
</form>
</div>
    };
}

sub display_marker_page {
    my $participant_id = $q->param('participant_id');

    print qq{
<div class="titlebox"><p align="center">MARKER DAYS</p></div>
Before you are presented with the calendar, please take a moment to recall
certain holidays, birthdays, newsworthy events and other personal
events that are meaningful to you. These (whether involving alcohol use or not) can assist in recall of your behavior over the past three
months. Please consider national holidays (such as Labor Day [September 6th],
Columbus Day [October 11th], Halloween [October 31st]), important school dates
like the day you moved back to campus and the day classes started, major
sporting events like Huskies Football games, major news events, your own or
others' birthdays, vacation beginning and end dates, or other dates of
important personal events (such as changing jobs, buying a house, starting a
new romantic relationship, a breakup).
<br /><br />
Please enter up to 10 personal marker days. An example is provided:
<br /><br />
<table  border="1" cellspacing="0" cellpadding="0">
<tr><td>
<form action="$SELF" method="POST">
<table border="0" cellspacing="1" cellpadding="4">
<tr bgcolor="#cccccc"><td>&nbsp;</td><td><strong>Date</strong></td><td><strong>Event</strong></td></tr>
<tr bgcolor="#eeeeee"><td><i>Example</i></td><td> 7/31</td><td> my birthday</td></tr>
    };

    my $rowcolor = 'dddddd';

    for my $rowcount (1..10) {
        print qq{
            <tr bgcolor="#$rowcolor"><td>$rowcount.</td>
            <td>
            <select name="${DATE_FORM_MM}_$rowcount"> 
        };
        print qq{<option value="0">Select month</option>\n};
        foreach my $month (1..12) {
            print qq{<option value="$month">$months{$month}</option>\n};
        }

        print qq{</select> <select name="${DATE_FORM_DD}_$rowcount"> 
             <option value="0">Day</option>
        };

        foreach my $day (1..31) {
            print qq{<option value="$day">$day</option>\n};
        }

        print qq{</select></td>
            <td><input size="30" type="text" name="description_$rowcount"></td>
            </tr>
        };

        $rowcolor = $rowcolor eq 'dddddd' ? 'eeeeee' : 'dddddd';
    }

    print qq{
</table>
</td></tr></table>
<br />
<input type="hidden" name="action" value="$PROCESS_ADD_MARKER">
<input type="hidden" name="participant_id" value="$participant_id">
<input type="submit" value="Done with markers">
</form>
    };
}

sub print_footer {
    print '</div>';
    print $q->end_html;
}

sub print_header {
    print $q->header;
    print qq{
<html>

<head>
<link rel="stylesheet" href="/css/reset_base.css" type="text/css">
<link rel="stylesheet" href="/css/global.css" type="text/css">
<title>TLFB Study</title>
</head>

<body>
<div id="main">
<div id="uwbar">
<div id="logo">
<p align="center"> <img src="http://www.uvabrand.com/assets/images/printLogo.jpg" alt="UVa Health System Logo" width="200"></p>
</div>
<br>
 <div id="pagetitle">
<p align="center">eHealth+ Online TLFB Alcohol Usage Calendar</p>
 </div>
<p align="center"><a href="$homepage">HOME</a></p>
</div>
<br />
<div class="outlinebox">
    };
}

sub print_instructions {
    print qq{
<strong>Each day</strong> should contain a "0" for no alcohol use or <strong>other number of drinks had.</strong><br><br>
<p align = "center"><strong>1 STANDARD DRINK IS EQUAL TO:</strong></p>
<ul>
<li>One <strong>12 oz.</strong> can/bottle of beer</li>
<li>One <strong>5 oz.</strong> glass of regular wine</li>
<li><strong>1 1/2 oz.</strong> of hard liquor (e.g. rum, vodka, whiskey)</li>
<li>One mixed or straight drink with <strong>1 1/2 oz.</strong> hard liquor</li>
</ul>
You can fill out each month of the calendar one at a time, or jump
around if it is easier for you to remember. You can click "previous month" or
"next month" to shuffle between months. 
<br /><br />Please make sure to fill
out all 90 days of the calendar. On the final page of the calendar, you will be
able to click "calendar complete" to advance to the next portion of the
assessment.
<br />
<br />

</font>
    };
}

    
sub page_one {
    my $participant_id = $q->param('participant_id');

    if ($participant_id) {
        $dispatch{$DISPLAY_INSTRUCTIONS}->();
    } else {
        print qq{
        <form action="$SELF" method="POST">
        ENTER YOUR PARTICIPANT ID TO BEGIN:  <input type="text" name="participant_id">
        <br />
        <br />
        <input type="hidden" name="action" value="$DISPLAY_INSTRUCTIONS">
        <input type="submit" value="Begin">
        </form>
        };
    }
}

sub make_date {
    my $rh_date = shift;
    my $date = join('/', $rh_date->{mm}, $rh_date->{dd});
    return $date;
}

sub process_calendar {
    my ($participant_id, $start_date, $stop_date) = @_;

    print "SAVING Calendar Data for participant '$participant_id'...  ";

    my $insert_sql = <<End_of_SQL;
INSERT INTO tlfb
(participant_id, date, drinks, hours, joints)
VALUES
(?, ?, ?, ?, ?)
End_of_SQL

    my $sth = $dbh->prepare($insert_sql) 
                  or die "Couldn't prepare insert: " . $dbh->errstr;

    my $current_date = $start_date;
    while ($current_date <= $stop_date) {
        my $drink_val  = $q->param("${DRINKS_FORM}_$current_date") || 0;
        my $hours_val  = $q->param("${HOURS_FORM}_$current_date")  || 0;
        my $joints_val = $q->param("${JOINTS_FORM}_$current_date") || 0;

        $sth->execute($participant_id, $current_date, $drink_val, $hours_val, $joints_val)
            or die "Couldn't execute for day $current_date: " . $sth->errstr;

        $current_date = UnixDate(DateCalc($current_date, "+1 days"), "%Y%m%d");
    }

    print qq{
      DONE!
        <br />
        <br />
<a href="$homepage">Back to the online TLFB homepage</a>
    };

}
