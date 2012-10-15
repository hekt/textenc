(function($) {
  $(function() {
    var root_url = document.documentElement.getAttribute('data-rootUrl');
    var rec_url = document.documentElement.getAttribute('data-receivedUrl');

    $("#bookmarklet_text")
      .focus(function() { $(this).select(); })
      .mouseup(function(e) { e.preventDefault(); });

  });
})(jQuery);
