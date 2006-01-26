<%

my($beginning, $ending) = FS::UI::Web::parse_beginning_ending($cgi);

my $join_cust = "
    JOIN cust_bill USING ( invnum )
    LEFT JOIN cust_main USING ( custnum )
";

my $join_pkg = "
    LEFT JOIN cust_pkg USING ( pkgnum )
    LEFT JOIN part_pkg USING ( pkgpart )
";

my $join = "
    JOIN cust_bill_pkg USING ( billpkgnum )
    $join_cust
    $join_pkg
";

my $where = "
  WHERE _date >= $beginning AND _date <= $ending
";
#    AND payby != 'COMP'

if ( $cgi->param('agentnum') =~ /^(\d+)$/ ) {
  $where .= " AND agentnum = $1 ";
}

if ( $cgi->param('out') ) {

  $where .= "
    AND 0 = (
      SELECT COUNT(*) FROM cust_main_county AS county_out
      WHERE (    county_out.county  = cust_main.county
              OR ( county_out.county IS NULL AND cust_main.county  =  '' )
              OR ( county_out.county  =  ''  AND cust_main.county IS NULL)
              OR ( county_out.county IS NULL AND cust_main.county IS NULL)
            )
        AND (    county_out.state   = cust_main.state
              OR ( county_out.state  IS NULL AND cust_main.state  =  ''  )
              OR ( county_out.state   =  ''  AND cust_main.state IS NULL )
              OR ( county_out.state  IS NULL AND cust_main.state IS NULL )
            )
        AND county_out.country = cust_main.country
        AND county_out.tax > 0
    )
  ";

} elsif ( $cgi->param('country' ) ) {

  my $county  = dbh->quote( $cgi->param('county')  );
  my $state   = dbh->quote( $cgi->param('state')   );
  my $country = dbh->quote( $cgi->param('country') );
  $where .= "
    AND ( county  = $county OR $county = '' )
    AND ( state   = $state  OR $state = '' )
    AND   country = $country
  ";
  $where .= ' AND taxclass = '. dbh->quote( $cgi->param('taxclass') )
    if $cgi->param('taxclass');

}

my $count_query = "SELECT COUNT(*), SUM(amount)".
                  "  FROM cust_tax_exempt_pkg $join $where";

my $query = {
  'table'     => 'cust_tax_exempt_pkg',
  'addl_from' => $join,
  'hashref'   => {},
  'select'    => join(', ',
                   'cust_tax_exempt_pkg.*',
                   #'cust_bill_pkg.*',
                   #'cust_bill._date',
                   #'part_pkg.pkg',
                   'cust_main.custnum',
                   FS::UI::Web::cust_sql_fields(),
                 ),
  'extra_sql' => $where,
};

my $ilink = [ "${p}view/cust_bill.cgi?", 'invnum' ];
my $clink = [ "${p}view/cust_main.cgi?", 'custnum' ];

my $conf = new FS::Conf;
my $money_char = $conf->config('money_char') || '$';

%><%= include( 'elements/search.html',
                 'title'       => 'Tax exemptions',
                 'name'        => 'tax exemptions',
                 'query'       => $query,
                 'count_query' => $count_query,
                 'count_addl'  => [ $money_char. '%.2f total', ],
                 'header'      => [
                   '#',
                   'Date',
                   'Amount',

                   #'Description',
                   #'Setup charge',
                   #'Recurring charge',
                   #'Invoice',
                   #'Date',

                   FS::UI::Web::cust_header(),
                 ],
                 'fields'      => [
                   'exemptpkgnum',
                   sub { $_[0]->month. '/'. $_[0]->year; },
                   'amount',

                   #sub { $_[0]->pkgnum > 0
                   #        ? $_[0]->get('pkg')
                   #        : $_[0]->get('itemdesc')
                   #    },
                   ##strikethrough or "N/A ($amount)" or something these when
                   ## they're not applicable to pkg_tax search
                   #sub { sprintf($money_char.'%.2f', shift->setup ) },
                   #sub { sprintf($money_char.'%.2f', shift->recur ) },
                   #'invnum',
                   #sub { time2str('%b %d %Y', shift->_date ) },

                   \&FS::UI::Web::cust_fields,
                 ],
                 'links'       => [
                   '',
                   '',
                   '',

                   #'',
                   #'',
                   #'',
                   #'',
                   #$ilink,
                   #$ilink,

                   ( map { $clink } FS::UI::Web::cust_header() ),
                 ],
                 'align' => 'rrr', # 'rlrrrc',
           )
%>

