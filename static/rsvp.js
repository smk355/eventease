document.addEventListener('DOMContentLoaded', function(){
    const vitYes = document.getElementById('vit_yes');
    const vitNo = document.getElementById('vit_no');
    const regField = document.getElementById('registration_field');
    const collegeField = document.getElementById('college_field');
    
    function updateFields(){
        if(vitYes.checked){
            regField.style.display = 'block';
            collegeField.style.display = 'none';
        } else if(vitNo.checked){
            regField.style.display = 'none';
            collegeField.style.display = 'block';
        } else {
            regField.style.display = 'none';
            collegeField.style.display = 'none';
        }
    }
    
    if(vitYes) {
        vitYes.addEventListener('change', updateFields);
    }
    if(vitNo) {
        vitNo.addEventListener('change', updateFields);
    }
});
