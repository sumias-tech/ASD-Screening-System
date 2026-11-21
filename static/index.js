let form=document.getElementById( "studentform");
form.addEventListener("submit", function(event){
    alert("working")

    if(document.getElementById("age").value==""){
        alert("please provide your name");
        document.studentform.age.focus();
        return false;

    }

document.getElementById("birthdate").addEventListener("change",function(){
    const birthdate = new Date(this.value);
    const today = new Date();
    let age = today.getFullYear() - birthdate.getFullYear();
    const monthdiff = today.getMonth() - birthdate.getMonth();
    if(monthdiff < 0 || (monthdiff === 0 && today.getDate() < birthdate.getdate())) {
        age--;
    }
    document.getElementById("age").value = age; 
})





})
