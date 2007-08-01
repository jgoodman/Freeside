<% include("/elements/header.html","Customer View: ". $cust_main->name ) %>

% if ( $curuser->access_right('Edit customer') ) { 
  <A HREF="<% $p %>edit/cust_main.cgi?<% $custnum %>">Edit this customer</A> | 
% } 

<SCRIPT TYPE="text/javascript" SRC="<%$fsurl%>elements/overlibmws.js"></SCRIPT>
<SCRIPT TYPE="text/javascript" SRC="<%$fsurl%>elements/overlibmws_iframe.js"></SCRIPT>
<SCRIPT TYPE="text/javascript" SRC="<%$fsurl%>elements/overlibmws_draggable.js"></SCRIPT>
<SCRIPT TYPE="text/javascript" SRC="<%$fsurl%>elements/iframecontentmws.js"></SCRIPT>

<SCRIPT TYPE="text/javascript">
function areyousure(href, message) {
  if (confirm(message) == true)
    window.location.href = href;
}
</SCRIPT>

% if ( $curuser->access_right('Cancel customer')
%        && $cust_main->ncancelled_pkgs
%      ) {

  <% cust_cancel_link($cust_main) %> | 

% } 

% if ( $conf->exists('deletecustomers')
%        && $curuser->access_right('Delete customer')
%      ) {
  <A HREF="<% $p %>misc/delete-customer.cgi?<% $custnum%>">Delete this customer</A> | 
% } 

% unless ( $conf->exists('disable_customer_referrals') ) { 
  <A HREF="<% $p %>edit/cust_main.cgi?referral_custnum=<% $custnum %>">Refer a new customer</A> | 
  <A HREF="<% $p %>search/cust_main.cgi?referral_custnum=<% $custnum %>">View this customer's referrals</A>
% } 

<BR><BR>

% if (    $curuser->access_right('Billing event reports') 
%      || $curuser->access_right('View customer billing events')
%    ) {

  <A HREF="<% $p %>search/cust_event.html?custnum=<% $custnum %>">View billing events for this customer</A>
  <BR><BR>

% }

%my $signupurl = $conf->config('signupurl');
%if ( $signupurl ) {
  This customer's signup URL: <A HREF="<% $signupurl %>?ref=<% $custnum %>"><% $signupurl %>?ref=<% $custnum %></A><BR><BR>
% } 


<A NAME="cust_main"></A>
<TABLE BORDER=0>
<TR>
  <TD VALIGN="top">
    <% include('cust_main/contacts.html', $cust_main ) %>
  </TD>
  <TD VALIGN="top" STYLE="padding-left: 54px">
    <% include('cust_main/misc.html', $cust_main ) %>
% if ( $conf->config('payby-default') ne 'HIDE' ) { 

      <BR>
      <% include('cust_main/billing.html', $cust_main ) %>
% } 

  </TD>
</TR>
</TABLE>
%
%if ( $cust_main->comments =~ /[^\s\n\r]/ ) {
%

<BR>
Comments
<% ntable("#cccccc") %><TR><TD><% ntable("#cccccc",2) %>
<TR>
  <TD BGCOLOR="#ffffff">
    <PRE><% encode_entities($cust_main->comments) %></PRE>
  </TD>
</TR>
</TABLE></TABLE>
% } 
<BR><BR>
% my $notecount = scalar($cust_main->notes());
% if ( ! $conf->exists('cust_main-disable_notes') || $notecount) {

<A NAME="cust_main_note"><FONT SIZE="+2">Notes</FONT></A><BR>
%   if ( $curuser->access_right('Add customer note') &&
%        ! $conf->exists('cust_main-disable_notes')
%      ) {

  <A HREF="javascript:void(0);" onClick="overlib( OLiframeContent('<% $p %>edit/cust_main_note.cgi?custnum=<% $cust_main->custnum %>', 616, 386, 'cust_main_note_popup' ), CAPTION, 'Enter customer note', STICKY, AUTOSTATUSCAP, MIDX, 0, MIDY, 0, DRAGGABLE, CLOSECLICK); return false;">Add customer note</A>

%   }

<BR>

%   if ($notecount) {

<iframe src="<% $p %>view/cust_main/notes.html?custnum=<% $cust_main->custnum %>" height="186" width="616" name="cust_main_notes" frameborder="0" marginborder="0" marginheight="0" scrolling="auto">
  <div><br>[iframe not supported]<br><br></div>
</iframe>

%   }else{ # make firefox happy wrt POSTDATA

<iframe src="<% $p %>view/cust_main/notes.html?custnum=<% $cust_main->custnum %>" height="24" width="616" name="cust_main_notes" frameborder="0" marginborder="0" marginheight="0" scrolling="auto">
  <div><br>[iframe not supported]<br><br></div>
</iframe>

%   }

% }


% if ( $conf->config('ticket_system') ) { 

  <BR><BR>
  <% include('cust_main/tickets.html', $cust_main ) %>
% } 


<BR><BR>

% #XXX enable me# if ( $curuser->access_right('View customer packages') { 
<% include('cust_main/packages.html', $cust_main ) %>
% #}

% if ( $conf->config('payby-default') ne 'HIDE' ) { 
  <% include('cust_main/payment_history.html', $cust_main ) %>
% } 


<% include('/elements/footer.html') %>
<%init>

my $curuser = $FS::CurrentUser::CurrentUser;

die "access denied"
  unless $curuser->access_right('View customer');

my $conf = new FS::Conf;

die "No customer specified (bad URL)!" unless $cgi->keywords;
my($query) = $cgi->keywords; # needs parens with my, ->keywords returns array
$query =~ /^(\d+)$/;
my $custnum = $1;
my $cust_main = qsearchs( {
  'table'     => 'cust_main',
  'hashref'   => { 'custnum' => $custnum },
  'extra_sql' => ' AND '. $curuser->agentnums_sql,
});
die "Customer not found!" unless $cust_main;

</%init>
<%once>


sub cust_cancel_link { cust_popup_link( 'misc/cancel_cust.html',
                                        'Cancel&nbsp;this&nbsp;customer',
                                        'Confirm Cancellation',
                                        '#ff0000',
                                        @_,
                                      );
}

#false laziness w/view/cust_main/packages.html

sub cust_popup_link {
  my($action, $label, $actionlabel, $color, $cust_main) = @_;
  $action .= '?'. $cust_main->custnum;
  popup_link($action, $label, $actionlabel, $color);
}

sub popup_link {
  my($action, $label, $actionlabel, $color) = @_;
  $color ||= '#333399';
  qq!<A HREF="javascript:void(0);" onClick="overlib( OLiframeContent('$p$action', 540, 336, 'pkg_or_svc_action_popup' ), CAPTION, '$actionlabel', STICKY, AUTOSTATUSCAP, MIDX, 0, MIDY, 0, DRAGGABLE, CLOSECLICK, BGCOLOR, '$color', CGCOLOR, '$color', CLOSETEXT, '' ); return false;">$label</A>!;

# CLOSETEXT, '', 
#WIDTH, 576, HEIGHT, 128, TEXTSIZE, 3,
#BGCOLOR, '#ff0000', CGCOLOR, '#ff0000'
}

</%once>
