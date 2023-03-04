const eyeicon = document.querySelector('#eyeicon')
const eyeicon2 = document.querySelector('#eyeicon2')
const password = document.querySelector('.pass')
const password2 = document.querySelector('.pass2')
const email = document.querySelector('.email')
const email_label = document.querySelector('.email_label')
const em = document.querySelector('.em')
const line = document.querySelector('.line')

eyeicon.addEventListener('click', () => {
    
    if(password.type == "password"){
        password.type = "text";
        eyeicon.classList.remove('fa-eye-slash');
        eyeicon.classList.add('fa-eye');
    }else{
        password.type = "password";

        eyeicon.classList.remove('fa-eye');
        eyeicon.classList.add('fa-eye-slash');
    }
})
eyeicon2.addEventListener('click', () => {
    if(password2.type == "password"){
        password2.type = "text";
        eyeicon2.classList.remove('fa-eye-slash');
        eyeicon2.classList.add("fa-eye");
    }else{
        password2.type = "password";

        eyeicon2.classList.add("fa-eye-slash");
        eyeicon2.classList.remove("fa-eye");
    }
})

// email.addEventListener('click', () => {
//     email.classList.toggle('active')


// })

if(document.readyState == 'loading'){
    document.addEventListener('DOMContentLoaded', ready)
}else{
    ready()
}

function ready() {

    if(email.value == ""){
        em.classList.remove('active')
        line.classList.remove('active')
    }else{
        console.log('sad')
        em.classList.add('active')
        line.classList.add('active')
    }
}
email.addEventListener('change', () => {
    if(email.value == ""){
        em.classList.remove('active')
        line.classList.remove('active')
    }else{
        em.classList.add('active')
        line.classList.add('active')
    }
})