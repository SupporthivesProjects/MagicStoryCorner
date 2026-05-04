<?php include 'includes/header.php'; ?>

        <section style="padding: 0%;">
            <div class="login_div">
                <div class="sign_outer">
                    <h2 class="head_login">Sign up</h2>
                    <div class="login_inner">
                        <div class="login_form w-100">
                            <div class="sign_div">
                                <input type="text" class="login_input w-100" placeholder="Enter your email">
                                <input type="text" class="login_input w-100" placeholder="Enter your email">
                            </div>
                            <div class="sign_div">
                                <input type="text" class="login_input w-100" placeholder="Enter your email">
                                <input type="text" class="login_input w-100" placeholder="Enter your email">
                            </div>
                        </div>
                        <div class="form-check sign_check_main">
                            <input class="form-check-input sign_check" type="checkbox" value="" id="checkDefault">
                            <label class="form-check-label sing_check_para" for="checkDefault">
                               I have read and agree to the <span>Terms of Use.</span>  
                            </label>
                        </div>
                        <div class="btn_div_sign w-100">
                            <img src="./img/not_robo.png" alt="" width="222.273px" height="56.41px">
                            <button type="button" class="btn btn_login" data-bs-toggle="modal" data-bs-target="#exampleModal">
                                Create account
                            </button>
                        </div>
                        <p class="para_login2">Already have an account? <a href="sign_in.html">Sign in</a></p>
                    </div>
                </div>
            </div>
        </section>
        <!-- Button trigger modal -->

<!-- Modal -->
        <div class="modal fade" id="exampleModal" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content modal_sign">
                <img src="./img/modal_Sign_up.png" alt="" style="z-index: 1;">
                <div class="sing_modal_main">
                    <div class="modal_sign_inner1">
                        <h3 class="head_sign_modal">Confirmation email sent!</h3>
                        <p class="para_modal_sign">All that’s left is to check your inbox or junk email in order to verify your account.</p>
                    </div>
                    <button type="button" class="btn sign_modal_btn_out" data-bs-dismiss="modal">
                        <img src="./img/sign_btn_upper.png" alt="">
                        <div class="sign_modal_btn_inn">
                            <img src="./img/sign_btn_L.png" alt="">
                                <div class="sing_modal_btn_main">Close</div>
                            <img src="./img/sign_btn_R.png" alt="">
                        </div>
                        <img src="./img/sign_btn_lower.png" alt="" style="margin-top: -39px;">
                        
                    </button>
                </div>
                <img src="./img/modal_sign_down.png" alt="" style="margin-top: -24px;">
            </div>
        </div>
        </div>

<?php include 'includes/footer.php'; ?>