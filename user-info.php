<?php include 'includes/header.php'; ?>

<section class="checkout-page">
<div class="user-info">
    <div class="billing-info">
        <h1 class="ub-h1">
            Billing information
        </h1>
        <div class="ab-field w-100">
            <div class="field-box">
                <h2 class="ay-txt">
                    About You
                </h2>
                <input type="text" placeholder="First name" class="inp-bx">
                <input type="text" placeholder="Last name" class="inp-bx">
                <input type="email" placeholder="Email Address" class="inp-bx">
            </div>
            <div class="field-box">
                <h2 class="ay-txt">
                    Address
                </h2>
                <input type="text" placeholder="Address line 1" class="inp-bx">
                <input type="text" placeholder="Address line 1" class="inp-bx">
                <div class="ap-b">
                <input type="text" placeholder="City / town" class="inp-bx">
                <input type="text" placeholder="Zip / Postal Code" class="inp-bx">
                </div>
            </div>
        </div>
         <div class="button-sec">
                    <button class="yello-btn btn">
                        <a href="#">Cancel</a>
                    </button>
                    <button class="bluee-btn btn">
                        <a href="#">Next: Cart Summary</a>
                    </button>
        </div>
    </div>
</div>
<img src="img/usr-info-mb.png" class="d-block d-md-none" alt="">
</section>

<?php include 'includes/footer.php'; ?>
