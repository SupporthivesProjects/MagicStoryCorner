<?php include 'includes/header.php'; ?>
<section class="contact-scroll-section">

    <div class="container">
        <div class="contact-flex">

            <div class="contact-scroll-wrapper">

                <!-- Contact Info -->
                <div class="contact-info-box">
                    <h5 class="contact-title">CONTACT INFORMATION</h5>
                    <p>123 place, City, Country, Post code</p>
                    <p>Contact@Magicstorycorner.com</p>
                    <p>+44 (0) 20 1234 5678</p>
                </div>

                <!-- Heading -->
                <h4 class="contact-heading">GET IN TOUCH</h4>

                <!-- Form -->
                <form class="contact-form">

                    <div class="contact-row">
                        <input type="text" class="contact-input" placeholder="First Name">
                        <input type="text" class="contact-input" placeholder="Last Name">
                    </div>

                    <div class="contact-row">
                        <input type="email" class="contact-input" placeholder="Email Address">
                        <input type="text" class="contact-input" placeholder="Phone number">
                    </div>

                    <div class="contact-row">
                        <textarea class="contact-textarea" placeholder="Your message"></textarea>
                    </div>
                    <div class="custom-checkbox">
                        <input type="checkbox" id="terms">
                        <label for="terms">
                            <span class="checkmark"></span>
                        </label>
                        <p class="termms"> I have read and agree to the
                            <a href="#">Terms of Use.</a>
                        </p>
                    </div>
                    <div class="contact-btn-wrap">
                        <img src="./img/cap.png" alt="" class="captcha">
                        <button type="button" class="contact-submit-btn" data-bs-toggle="modal"
                            data-bs-target="#contactSuccessModal">
                            SUBMIT MESSAGE
                        </button>
                    </div>

                </form>

            </div>

        </div>
    </div>

</section>

<!-- CONTACT SUCCESS MODAL -->
<div class="modal fade" id="contactSuccessModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">

        <div class="modal-content contact_modal_wrapper">

            <div class="contact_modal_body text-center">

                <h2 class="contact_modal_title">
                    CONTACT REQUEST <br> SUBMITTED
                </h2>

                <p class="contact_modal_text">
                    We will get back to you shortly, make sure to check your junk mail just in case.
                </p>

                <!-- CLOSE BUTTON (IMAGE BG) -->
                <button type="button" class="contact_modal_btn" data-bs-dismiss="modal">
                    CLOSE
                </button>

            </div>

        </div>

    </div>
</div>
<?php include 'includes/footer.php'; ?>