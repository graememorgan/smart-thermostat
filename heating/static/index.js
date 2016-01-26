// scripts for the index page

// updates the current boiler status (firing or not firing) as well as
// whether it's overriden to ON/OFF, or on auto mode.
updateBoiler = function() {
  $.get("/boiler/state", function(data) {
    data = JSON.parse(data);
    $("#boiler-image").toggleClass("on", !!data);
  });

  $.get("/boiler/setpoint", function(data) {
    data = JSON.parse(data);
    if (!data[0]) {
      $("#boiler-override").hide();
      $("#boiler-switch").slider("value", 1);
      $("#boiler-status").show().html("Setpoint is " + data[1] + "&deg;C");
    } else {
      $("#boiler-override").show();
      $("#boiler-status").hide();
      $("#boiler-switch").slider("value", data[1] == 0 ? 0 : 2);
      $("#boiler-override-temperature").val(data[1]);
      $("#boiler-override-remaining").val(Math.round(data[2] / 60));
    }
  });
};

// updates the current temperature/RH for each location
updateCurrent = function() {
  $.get("/current", function(data) {
    data = JSON.parse(data);
    $.each(data, function(location, quantities) {
      $.each(quantities, function(quantity, value) {
        $("#location-" + location + " dd." + quantity + " span").html(value);
      });
    });
  });
};

$(function() {
  $("#boiler-switch").slider({
    value:0,
    min: 0,
    max: 2,
    step: 1,
    change: function(event, ui) {
      console.log(ui.value);
      $(this).removeClass("off auto on").addClass(["off", "auto", "on"][ui.value]);
      if (!event.originalEvent) return;
      // 0 = off
      // 1 = auto
      // 2 = on
      var value = ui.value;

      if (value == 0) {
        $.post("/boiler/override", {setpoint: 0, remaining: 30}, updateBoiler);
      } else if (value == 1) {
        $.post("/boiler/override", {}, updateBoiler);
      } else if (value == 2) {
        $.post("/boiler/override", {setpoint: 20, remaining: 30}, updateBoiler);
      }
    }
  });
  $("#boiler-override form").submit(function (e) {
    e.preventDefault();
    $.post("/boiler/override", {setpoint: $("#boiler-override-temperature").val(), remaining: $("#boiler-override-remaining").val()});
  });
  setInterval(updateBoiler, 10000);
  updateBoiler();
  setInterval(updateCurrent, 60000);
});

