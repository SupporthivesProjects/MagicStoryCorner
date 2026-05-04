<?php include 'includes/header.php'; ?>

        <section style="padding: 0%;">
            <div class="login_div">
                <div class="login_outer">
                    <h2 class="head_login">Set a password</h2>
                    <div class="login_inner">
                        <div class="login_form">
                            <input type="text" class="login_input" placeholder="New password">
                            <input type="text" class="login_input" placeholder="Confirm new password">
                        </div>
                        <button class="btn btn_login" data-bs-toggle="modal" data-bs-target="#exampleModal">
                            set new password
                        </button>
                    </div>
                </div>
            </div>
        </section>
        <div class="modal fade" id="exampleModal" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content modal_sign">
                <img src="./img/modal_Sign_up.png" alt="" style="z-index: 1;">
                <div class="sing_modal_main">
                    <div class="modal_sign_inner1">
                        <h3 class="head_sign_modal">Reset password email sent</h3>
                    </div>
                    <button type="button" class="btn btn_login" data-bs-dismiss="modal">Close</button>
                </div>
                <img src="./img/modal_sign_down.png" alt="" style="margin-top: -24px;">
            </div>
        </div>
        </div>


<?php include 'includes/footer.php'; ?>