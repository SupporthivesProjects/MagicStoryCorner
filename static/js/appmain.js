console.log(window.location.href)
$(window).scroll(function(){
    if ($(window).scrollTop() >= 100) {
        $('.header').addClass('add-header');
    }
    else {
        $('.header').removeClass('add-header');
    }
});
// change src

let countimg = 0;
let toogleBtn = document.querySelector('.navbar-toggler');

toogleBtn.addEventListener('click',()=>{
    if(countimg == 0){
        document.querySelector('.navbar-toggler-icon-mo').src ="/static/media/close.svg";
        document.querySelector(".header").classList.add('bottom-img-header');
      countimg = 1;
    }
    else{
        document.querySelector('.navbar-toggler-icon-mo').src ="/static/media/menu.svg";
        document.querySelector(".header").classList.remove('bottom-img-header');
        countimg = 0;
    }
})




// sldier home page

const buttons = document.querySelectorAll('.btnselect');
buttons.forEach(button => {
  button.addEventListener('click', function(e) {
    e.stopPropagation(); // Prevent if card also has click
    document.querySelectorAll('.price-card').forEach(c => c.classList.remove('active')); // Optional: remove active from others
    this.closest('.price-card').classList.add('active'); // Add active to parent card
  });
});



