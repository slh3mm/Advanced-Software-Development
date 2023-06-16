$(document).ready(function () {
    $("#classes").change(function () {
        var val = $(this).val();
        var str = "<option value='test'> " + val + " </option>";
        $("#mnemonic").html(str);
    });
});