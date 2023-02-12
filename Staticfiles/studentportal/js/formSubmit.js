$('#postForm').on('submit', function() {
    $(this).find('input[type="submit"]').attr('disabled','disabled');
});