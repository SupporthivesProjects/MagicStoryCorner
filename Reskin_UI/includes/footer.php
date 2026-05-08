<section class="footer-bg-top d-lg-block d-md-block d-none">
     <img src="./img/footer-top-bg.png" class="bg-image">
     <div class="container">
       <div class="row align-items-center">
          <div class="col-lg-9 col-md-12 col-sm-12 col-12 ">
            <p>To enjoy the ultimate experience, give our web app a try!</p>
          </div>
          <div class="col-lg-3 col-md-12 col-sm-12 col-12 ">
             <a href="#" class="btn btn-design">Scan QR code</a>
          </div>
       </div>
     </div>
</section>
  <footer class="footer position-relative">
    <img src="./img/footer-bg.png" class="bg-image img-fluid d-lg-block d-md-block d-none">
    <img src="./img/footer-img-mo.png" class="img-fluid d-lg-none d-md-none d-block">
    <img src="./img/footer-mo.png" class="bg-image img-fluid d-lg-none d-md-none d-block">
    <div class="container">
        <div class="col">
            <div class="row">
                <div class="col-lg-4 col-md-12 col-sm-12 col-12">
                  <div class="footer-logo">
                      <img src="./img/footer-logo.svg" alt="" class="img-fluid f-logo">
                      <p>© 2025 Magicstorycorner. All rights reserved.</p>
                      <img src="./img/Mastercard.svg" alt="" class="img-fluid">
                  </div>
                </div>
                <div class="col-lg-8 col-md-12 col-sm-12 col-12">
                   <div class="footer-right">
                      <div class="footer-row">
                          <div class="footer-menu">
                            <h6>information</h6>
                            <p>
                            info@magicstorycorner.com<br>
                            123-00-0000<br>
                            Company name, 123 place,<br>
                            City,  Country, Post code
                            </p>
                          </div>
                          <div class="footer-right-row">
                            <div class="footer-menu footer-menu-1 footer-menu-third">
                              <h6>Links</h6>
                              <ul>
                                <li>
                                  <a href="#">Stories</a>
                                </li>
                                <li>
                                  <a href="#">Create</a>
                                </li>
                                <li>
                                  <a href="#">Pricing</a>
                                </li>
                                <li>
                                  <a href="#">About us</a>
                                </li>
                                <li>
                                  <a href="#">How it works</a>
                                </li>
                                <li>
                                  <a href="#">Contact us</a>
                                </li>
                              </ul>
                            </div>
                            <div class="footer-menu footer-menu-2">
                              <h6>Policies</h6>
                                <ul>
                                  <li>
                                    <a href="#">Terms & conditions</a>
                                  </li>
                                  <li>
                                    <a href="#">Privacy policy</a>
                                  </li>
                                  <li>
                                    <a href="#">Cookie Policy</a>
                                  </li>
                                </ul>
                              </div>
                            </div>
                          </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
  </footer>
</div>
    <script src="uiframe/js/jquery.min.js"></script>
    <script src="uiframe/js/bootstrap.bundle.min.js"></script>
    <script src="uiframe/js/popper.min.js"></script>
    <script src="uiframe/js/slick.js"></script>
    <script src="uiframe/js/owl.carousel.js"></script>
    <script src="uiframe/js/swiper-bundle.min.js"></script>
    <script src="uiframe/js/flickity.pkgd.min.js"></script>   
    <script src="uiframe/js/aos.js"></script>
    <script src="./uiframe/js/home-js.js"></script>
    <script>
      $(document).ready(function () {
          $(".navbar-toggler").click(function () {
              $(this).toggleClass("is-active");
              $(".navbar-expand-lg").toggleClass("header-is-active");

              let logo = $("#logo");
              if (logo.attr("src") === "./img/logo.svg") {
                  logo.attr("src", "./img/logo.svg");
              } else {
                  logo.attr("src", "./img/logo.svg");
              }
          });
      });
    </script>
    <script>
      $('#filterid').on('click', function(event) {
          $('#filterBox').slideToggle(300);
          $('#filterBox').toggleClass('open');
          event.preventDefault();
      });
      $(document).ready(function(){
        $("#filter-close").click(function(){
          $("#filterBox").slideUp("slow");
        });
      });
      document.querySelectorAll(".ul-filter-menu h3").forEach(header => {
        header.addEventListener("click", () => {
          const body = header.nextElementSibling;

          body.classList.toggle("open");     // toggle body
          header.classList.toggle("active"); // toggle class on h3
        });
      });
    </script>
    <script>
      function selectCurrency(currency, flagSrc) {
          const btn = document.getElementById("currencyBtn");
          const flag = document.getElementById("currencyFlag");
          btn.innerHTML = `${currency} <img id="currencyFlag" src="${flagSrc}" class="img-fluid">`;
      }
    </script>
    <script>
      window.addEventListener('scroll', function() {
          var content = document.querySelector('header');
          var scrollPosition = window.scrollY;
          if (scrollPosition > 10) {
              content.classList.add("header-scroll")
          } else {
              content.classList.remove("header-scroll")
          }
      });
    </script>
    <script>
      AOS.init();
    </script>
</body>
</html>
  