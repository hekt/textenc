(function($) {
  $(function() {
    var root_url = document.documentElement.getAttribute('data-rootUrl');
    var rec_url = document.documentElement.getAttribute('data-receivedUrl');

    // hide submit button when javascript enabled
    $("#form_unspecified input[type='submit']").css("display", "none");

    var l;
    $("select#select_encoding").change(function() {
      if ($(this).val() !== '0') {
        var l = root_url + $(this).val() + "/" + rec_url;
        window.location = l;
      }
    });

  });
})(jQuery);
