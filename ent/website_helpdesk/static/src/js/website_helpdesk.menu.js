odoo.define("website_helpdesk.menu", function (require) {
    "use strict";

    require("web.dom_ready");

    var pathname = $(window.location).attr("pathname");
    var $link = $(".team_menu li a");
    if (pathname !== "/helpdesk/") {
        $link = $link.filter("[href$='" + pathname + "']");
    }
    $link.first().closest("li").addClass("active");

});
