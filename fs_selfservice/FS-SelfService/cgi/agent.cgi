#!/usr/bin/perl -Tw

#some false laziness w/selfservice.cgi

use strict;
use vars qw($cgi $session_id $form_max $template_dir);
use subs qw(do_template);
use CGI;
use CGI::Carp qw(fatalsToBrowser);
use Business::CreditCard;
use Text::Template;
use FS::SelfService qw( agent_login agent_info
                        agent_list_customers
                        signup_info new_customer
                        customer_info order_pkg
                      );

$template_dir = '.';

$form_max = 255;

$cgi = new CGI;

unless ( defined $cgi->param('session') ) {
  do_template('agent_login',{});
  exit;
}

if ( $cgi->param('session') eq 'login' ) {

  $cgi->param('username') =~ /^\s*([a-z0-9_\-\.\&]{0,$form_max})\s*$/i
    or die "illegal username";
  my $username = $1;

  $cgi->param('password') =~ /^(.{0,$form_max})$/
    or die "illegal password";
  my $password = $1;

  my $rv = agent_login(
    'username' => $username,
    'password' => $password,
  );
  if ( $rv->{error} ) {
    do_template('agent_login', {
      'error'    => $rv->{error},
      'username' => $username,
    } );
    exit;
  } else {
    $cgi->param('session' => $rv->{session_id} );
    $cgi->param('action'  => 'agent_main' );
  }
}

$session_id = $cgi->param('session');

$cgi->param('action') =~
   /^(agent_main|signup|process_signup|list_customers|view_customer|process_order_pkg)$/
  or die "unknown action ". $cgi->param('action');
my $action = $1;

warn "running $action\n";
my $result = eval "&$action();";
die $@ if $@;

if ( $result->{error} eq "Can't resume session" ) { #ick
  do_template('agent_login',{});
  exit;
}

warn "processing template $action\n";
do_template($action, {
  'session_id' => $session_id,
  %{$result}
});

#-- 

sub agent_main { agent_info( 'session_id' => $session_id ); }

sub signup { signup_info( 'session_id' => $session_id ); }

sub process_signup {

  my $init_data = signup_info( 'session_id' => $session_id );
  if ( $init_data->{'error'} ) {
    if ( $init_data->{'error'} eq "Can't resume session" ) { #ick
      do_template('agent_login',{});
      exit;
    } else { #?
      die $init_data->{'error'};
    }
  }

  my $error = '';

  #some false laziness w/signup.cgi
  my $payby = $cgi->param('payby');
  if ( $payby eq 'CHEK' || $payby eq 'DCHK' ) {
    #$payinfo = join('@', map { $cgi->param( $payby. "_payinfo$_" ) } (1,2) );
    $cgi->param('payinfo' => $cgi->param($payby. '_payinfo1'). '@'. 
                             $cgi->param($payby. '_payinfo2')
               );
  } else {
    $cgi->param('payinfo' => $cgi->param( $payby. '_payinfo' ) );
  }
  $cgi->param('paydate' => $cgi->param( $payby. '_month' ). '-'.
                           $cgi->param( $payby. '_year' )
             );
  $cgi->param('payname' => $cgi->param( $payby. '_payname' ) );
  $cgi->param('paycvv' => defined $cgi->param( $payby. '_paycvv' )
                            ? $cgi->param( $payby. '_paycvv' )
                            : ''
             );

  if ( $cgi->param('invoicing_list') ) {
    $cgi->param('invoicing_list' => $cgi->param('invoicing_list'). ', POST')
      if $cgi->param('invoicing_list_POST');
  } else {
    $cgi->param('invoicing_list' => 'POST' );
  }

  if ( $cgi->param('_password') ne $cgi->param('_password2') ) {
    $error = $init_data->{msgcat}{passwords_dont_match}; #msgcat
    $cgi->param('_password', '');
    $cgi->param('_password2', '');
  }

  if ( $payby =~ /^(CARD|DCRD)$/ && $cgi->param('CARD_type') ) {
    my $payinfo = $cgi->param('payinfo');
    $payinfo =~ s/\D//g;

    $payinfo =~ /^(\d{13,16})$/
      or $error ||= $init_data->{msgcat}{invalid_card}; #. $self->payinfo;
    $payinfo = $1;
    validate($payinfo)
      or $error ||= $init_data->{msgcat}{invalid_card}; #. $self->payinfo;
    cardtype($payinfo) eq $cgi->param('CARD_type')
      or $error ||= $init_data->{msgcat}{not_a}. $cgi->param('CARD_type');
  }

  unless ( $error ) {
    my $rv = new_customer ( {
      'session_id'       => $session_id,
      map { $_ => $cgi->param($_) }
        qw( last first ss company
            address1 address2 city county state zip country
            daytime night fax
            payby payinfo paycvv paydate payname invoicing_list
            pkgpart username sec_phrase _password popnum refnum
          ),
        grep { /^snarf_/ } $cgi->param
    } );
    $error = $rv->{'error'};
  }

  if ( $error ) { 
    $action = 'signup';
    my $r = { 
      $cgi->Vars,
      %{$init_data},
      'error' => $error,
    };
    #warn join('\n', map "$_ => $r->{$_}", keys %$r )."\n";
    $r;
  } else {
    $action = 'agent_main';
    my $agent_info = agent_info( 'session_id' => $session_id );
    $agent_info->{'message'} = 'Signup sucessful';
    $agent_info;
  }

}

sub list_customers {
  agent_list_customers( 'session_id' => $session_id,
                        map { $_ => $cgi->param($_) }
                          grep defined($cgi->param($_)),
                               qw(prospect active susp cancel)
                      );
}

sub view_customer {

  my $init_data = signup_info( 'session_id' => $session_id );
  if ( $init_data->{'error'} ) {
    if ( $init_data->{'error'} eq "Can't resume session" ) { #ick
      do_template('agent_login',{});
      exit;
    } else { #?
      die $init_data->{'error'};
    }
  }

  my $customer_info = customer_info (
    'agent_session_id' => $session_id,
    'custnum'          => $cgi->param('custnum')
  );


  return {
    ( map { $_ => $init_data->{$_} }
          qw( part_pkg security_phrase svc_acct_pop ),
    ),
    %$customer_info,
  };
}

sub process_order_pkg {

  my $results = '';

  if ( $cgi->param('_password') ne $cgi->param('_password2') ) {
    my $init_data = signup_info( 'session_id' => $session_id );
    $results = { error => $init_data->{msgcat}{passwords_dont_match} };
    $cgi->param('_password', '');
    $cgi->param('_password2', '');
  }

  $results ||= order_pkg (
    'agent_session_id' => $session_id,
    map { $_ => $cgi->param($_) }
        qw( custnum pkgpart username _password _password2 sec_phrase popnum )
  );

  $action = 'view_customer';
  $cgi->delete( grep { $_ ne 'custnum' } $cgi->param )
    unless $results->{'error'};

  return {
    $cgi->Vars,
    %{view_customer()},
    'message' => $results->{'error'}
                   ? '<FONT COLOR="#FF0000">'. $results->{'error'}. '</FONT>'
                   : 'Package order sucessful.'
  };

}

#--

sub do_template {
  my $name = shift;
  my $fill_in = shift;
  #warn join(' / ', map { "$_=>".$fill_in->{$_} } keys %$fill_in). "\n";

  $cgi->delete_all();
  $fill_in->{'selfurl'} = $cgi->self_url;
  $fill_in->{'cgi'} = \$cgi;

  my $template = new Text::Template( TYPE    => 'FILE',
                                     SOURCE  => "$template_dir/$name.html",
                                     DELIMITERS => [ '<%=', '%>' ],
                                     UNTAINT => 1,                    )
    or die $Text::Template::ERROR;

  print $cgi->header( '-expires' => 'now' ),
        $template->fill_in( PACKAGE => 'FS::SelfService::_agentcgi',
                            HASH    => $fill_in
                          );
}

package FS::SelfService::_agentcgi;
use FS::SelfService qw(regionselector expselect popselector);

