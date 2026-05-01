<?php include 'includes/header.php'; ?>

<style>
    section{
        padding: 0px;
    }
</style>

<section id="tab0" class="tab-content">
    <div class="age_section">
      <div class="container">
        <div class="age_div">
          <h1 class="age_title">Create  your story</h1>
          <form method="post" id="ageForm" style="min-width: 300px;">
            <input type="hidden" name="age" id="selectedAgeInput">
            <div class="age_bottom">
              <div class="age_droplabelbar">
                <div class="drop_labelbar">
                  <p class="drop_label">Child’s Age</p>
                  <img src="./img/question_icon.svg">
                </div>
                <div class="custom-dropdown" id="customDropdown">
                  <button type="button" class="dropdown-btn" id="dropdownButton">
                    <span class="dropdown-text age_droptext" id="selectedText">How old is the little one?</span>
                    <img src="./img/age_dropicon.svg" class="dropdown-icon" id="dropdownIcon">
                  </button>
                  <ul class="dropdown-list" id="ageList">
                      <li>1</li>
                      <li>2</li>
                      <li>3</li>
                  </ul>
                </div>
              </div>
              <button type="button" id="tab0Next" class="btn age_btn">Continue</button>
            </div>
          </form>
        </div>
      </div>
    </div>
</section>

<section class="story_section" id="storySectionContainer" style="display:none;">
    <div class="story-page" id="storyPage">
        <h1 class="age_title">Create your story</h1>
        <div class="prog_imgbar">
            <img class="progress_img" src="./img/progress_line.svg">
        </div>
        <div class="progressbar_main" id="progressBarMain">
            <div class="progress-bar progress_bar">
                <div class="step" id="step1">
                    <img id="diamond1" src="{% static 'media/diamond-glow.svg' %}" alt="">
                    <p id="title1">Make Your Hero</p>
                </div>
                <div class="step" id="step2">
                    <img id="diamond2" src="{% static 'media/diamond-normal.svg' %}" alt="">
                    <p id="title2">Build Your World</p>
                </div>
                <div class="step" id="step3">
                    <img id="diamond3" src="{% static 'media/diamond-normal.svg' %}" alt="">
                    <p id="title3">Choose Your Style</p>
                </div>
                <div class="step" id="step4">
                    <img id="diamond4" src="{% static 'media/diamond-normal.svg' %}" alt="">
                    <p id="title4">Select A Voice</p>
                </div>
            </div>
        </div>

        <div class="tab-content tab_content" id="tab1">
            <div class="tab_c1">
                <div class="tab_c1inner">
                    <img class="char_ani1" src="{% static 'media/char_ani1.svg' %}">
                    <img class="char_ani2" src="{% static 'media/char_ani2.svg' %}">
                    <input type="text" class="form-control story_textbox" id="char_name" placeholder="Enter character name">
                    <div class="char_textareamain">
                        <div class="char_textareatop">
                            <p class="textarea_label">What do they look like?<img src="./img/question_icon.svg"></p>
                            <p class="textarea_textcount" id="charLookCount">0/300</p>
                        </div>
                        <textarea class="form-control story_textarea" id="charLook" rows="3" maxlength="300" placeholder="Enter details about your character such as: species, size, clothing and any other physical details. The more the better!"></textarea>
                    </div>
                    <div class="char_btnbar">
                        <button type="button" class="btn char_btn1" id="tab1Back">Back</button>
                        <button type="button" class="btn char_btn2 char_btn2a" id="tab1Next">Next</button>
                    </div>
                </div>
            </div>
        </div>

        <div class="tab-content tab_content" id="tab2">
            <div class="tab_c2">
                <div class="tab_c2inner">
                    <img class="world_ani1" src="{% static 'media/world_ani1.svg' %}">
                    <img class="world_ani2" src="{% static 'media/world_ani2.svg' %}">

                    <div class="tab2_contbar">
                        <div class="char_textareatop">
                            <p class="textarea_label">Setting<img src="./img/question_icon.svg"></p>
                            <p class="textarea_textcount" id="settingCount">0/400</p>
                        </div>
                        <div class="setting-options" id="settingOptions">
                            <label class="option">
                                <input type="radio">
                                <span>🏰 Fairy tale</span>
                            </label>
                            <label class="option">
                                <input type="radio">
                                <span>🚀 Outer space</span>
                            </label>
                            <label class="option">
                                <input type="radio">
                                <span>🌲 Enchanted forest</span>
                            </label>
                            <label class="option">
                                <input type="radio">
                                <span>🎪 Circus</span>
                            </label>
                            <label class="option">
                                <input type="radio">
                                <span>🏝 Desert island</span>
                            </label>
                            <label class="option">
                                <input type="radio">
                                <span>🏙 Cityscape</span>
                            </label>
                            <label class="option">
                                <input type="radio">
                                <span>🏞 Nature</span>
                            </label>
                            <label class="option">
                                <input type="radio">
                                <span>🌆 Urban</span>
                            </label>
                            <label class="option">
                                <input type="radio">
                                <span>🏖 Beach</span>
                            </label>
                        </div>
                        <textarea class="form-control story_textarea" id="settingTextarea" rows="3" maxlength="400" placeholder="Enter a settings description."></textarea>
                    </div>

                    <div class="tab2_contbar">
                        <div class="char_textareatop">
                            <p class="textarea_label">Plot<img src="./img/question_icon.svg"></p>
                            <p class="textarea_textcount" id="plotCount">0/400</p>
                        </div>
                        <div class="setting-options" id="plotOptions">
                            <label class="option">
                                <input type="radio">
                                <span>🤪 Silly adventure</span>
                            </label>
                            <label class="option">
                                <input type="radio">
                                <span>✨ Magical find</span>
                            </label>
                            <label class="option">
                                <input type="radio">
                                <span>🏁 Epic race</span>
                            </label>
                            <label class="option">
                                <input type="radio">
                                <span>🦸 Rescue mission</span>
                            </label>
                            <label class="option">
                                <input type="radio">
                                <span>🕵️ Big mystery</span>
                            </label>
                            <label class="option">
                                <input type="radio">
                                <span>🤖 Robot world</span>
                            </label>
                            <label class="option">
                                <input type="radio">
                                <span>🌳 Forest adventure</span>
                            </label>
                            <label class="option">
                                <input type="radio">
                                <span>🏰 Castle quest</span>
                            </label>
                        </div>
                        <textarea class="form-control story_textarea" id="plotTextarea" rows="3" maxlength="400" placeholder="Enter your plot."></textarea>
                    </div>

                    <div class="tab2_contbar">
                        <div class="char_textareatop">
                            <p class="textarea_label">Theme<img src="./img/question_icon.svg"></p>
                            <p class="textarea_textcount" id="themeCount">0/400</p>
                        </div>
                        <div class="setting-options" id="themeOptions">
                            <label class="option">
                                <input type="radio">
                                <span>😂 Funny</span>
                            </label>
                            <label class="option">
                                <input type="radio">
                                <span>🦸 Heroes</span>
                            </label>
                            <label class="option">
                                <input type="radio">
                                <span>🌌 Space</span>
                            </label>
                            <label class="option">
                                <input type="radio">
                                <span>🐾 Animals</span>
                            </label>
                            <label class="option">
                                <input type="radio">
                                <span>🧙 Magic</span>
                            </label>
                            <label class="option">
                                <input type="radio">
                                <span>🤗 Friendship</span>
                            </label>
                            <label class="option">
                                <input type="radio">
                                <span>🌍 Exploration</span>
                            </label>
                            <label class="option">
                                <input type="radio">
                                <span>🐉 Dragon adventure</span>
                            </label>
                            <label class="option">
                                <input type="radio">
                                <span>🏖️ Beach vacation</span>
                            </label>
                        </div>
                        <textarea class="form-control story_textarea" id="themeTextarea" rows="3" maxlength="400" placeholder="And now the theme."></textarea>
                    </div>

                    <div class="char_btnbar">
                        <button type="button" class="btn char_btn1 back-btn" id="tab2Back">Back</button>
                        <button type="button" class="btn char_btn2 next-btn" id="tab2Next">Next</button>
                    </div>
                </div>
            </div>
        </div>

        <div class="tab-content tab_content" id="tab3">
            <div class="tab_c3">
                <div class="style_top">
                    <img class="tab3_ani" src="{% static 'media/style_ani.svg' %}">
                    <div class="tab3top_card">
                        <p class="textarea_label">Tone<img src="./img/question_icon.svg"></p>
                        <div class="setting-options tab3_options" id="toneOptions">
                            <label class="option">
                                <input type="radio" data-cost="{{ tone.cost }}" name="selected_tone" value="{{ tone.id }}">
                                <span>😀 Playful</span>
                            </label>
                            <label class="option">
                                <input type="radio" data-cost="{{ tone.cost }}" name="selected_tone" value="{{ tone.id }}">
                                <span>❤️ Heartwarming</span>
                            </label>
                            <label class="option">
                                <input type="radio" data-cost="{{ tone.cost }}" name="selected_tone" value="{{ tone.id }}">
                                <span>😀 Happy</span>
                            </label>
                            <label class="option">
                                <input type="radio" data-cost="{{ tone.cost }}" name="selected_tone" value="{{ tone.id }}">
                                <span>😂 Funny</span>
                            </label>
                            <label class="option">
                                <input type="radio" data-cost="{{ tone.cost }}" name="selected_tone" value="{{ tone.id }}">
                                <span>🤔 Serious</span>
                            </label>
                            <label class="option">
                                <input type="radio" data-cost="{{ tone.cost }}" name="selected_tone" value="{{ tone.id }}">
                                <span>🌟 Exciting</span>
                            </label>
                            <label class="option">
                                <input type="radio" data-cost="{{ tone.cost }}" name="selected_tone" value="{{ tone.id }}">
                                <span>😴 Calm</span>
                            </label>
                            <label class="option">
                                <input type="radio" data-cost="{{ tone.cost }}" name="selected_tone" value="{{ tone.id }}">
                                <span>😱 Scary</span>
                            </label>
                            <label class="option">
                                <input type="radio" data-cost="{{ tone.cost }}" name="selected_tone" value="{{ tone.id }}">
                                <span>😢 Sad</span>
                            </label>
                        </div>
                    </div>
                    <div class="tab3top_card">
                        <p class="textarea_label">Length of story<img src="./img/question_icon.svg"></p>
                        <div class="setting-options tab3_options" id="lengthOptions">
                            <label class="option">
                                <input type="radio" data-cost="{{ tone.cost }}" name="selected_tone" value="{{ tone.id }}">
                                <span>⚡ Short</span>
                            </label>
                            <label class="option">
                                <input type="radio" data-cost="{{ tone.cost }}" name="selected_tone" value="{{ tone.id }}">
                                <span>📖 Standard</span>
                            </label>
                            <label class="option">
                                <input type="radio" data-cost="{{ tone.cost }}" name="selected_tone" value="{{ tone.id }}">
                                <span>📚 Long</span>
                            </label>
                            <label class="option">
                                <input type="radio" data-cost="{{ tone.cost }}" name="selected_tone" value="{{ tone.id }}">
                                <span>🏰 Epic</span>
                            </label>
                        </div>
                    </div>
                </div>
                <div class="style_midouter">
                    <div class="style_mid">
                        <p class="textarea_label">Visual Image style<img src="./img/question_icon.svg"></p>
                        <div class="cards-container" id="styleCardsContainer">
                            <div class="card-item">
                                <img src="./img/story_style1.png" alt="">
                                <p class="card-title">3D cartoon</p>
                            </div>
                            <div class="card-item">
                                <img src="./img/story_style2.png" alt="">
                                <p class="card-title">Watercolor</p>
                            </div>
                            <div class="card-item">
                                <img src="./img/story_style3.png" alt="">
                                <p class="card-title">Comic book</p>
                            </div>
                            <div class="card-item">
                                <img src="./img/story_style4.png" alt="">
                                <p class="card-title">Photorealistic</p>
                            </div>
                            <div class="card-item">
                                <img src="./img/story_style5.png" alt="">
                                <p class="card-title">Sketch</p>
                            </div>
                            <div class="card-item">
                                <img src="./img/story_style6.png" alt="">
                                <p class="card-title">Oil painting</p>
                            </div>
                            <div class="card-item">
                                <img src="./img/story_style7.png" alt="">
                                <p class="card-title">Flat color</p>
                            </div>
                            <div class="card-item">
                                <img src="./img/story_style8.png" alt="">
                                <p class="card-title">Pixel Art</p>
                            </div>
                            <div class="card-item">
                                <img src="./img/story_style9.png" alt="">
                                <p class="card-title">Crayon color</p>
                            </div>
                            <div class="card-item">
                                <img src="./img/story_style10.png" alt="">
                                <p class="card-title">Vintage&nbsp;illustration</p>
                            </div>
                            <div class="card-item">
                                <img src="./img/story_style11.png" alt="">
                                <p class="card-title">paper cutout</p>
                            </div>
                            <div class="card-item">
                                <img src="./img/story_style12.png" alt="">
                                <p class="card-title">Embroidery</p>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="style_bottom">
                    <div class="char_btnbar">
                        <button type="button" class="btn char_btn1 back-btn" id="tab3Back">Back</button>
                        <button type="button" class="btn char_btn2 next-btn" id="tab3Next">Next</button>
                    </div>
                </div>
            </div>
        </div>

        <div class="tab-content tab_content" id="tab4">
            <div class="tab_c4">
                <div class="tab_c4inner">
                    <img class="voice_ani1" src="{% static 'media/voice_ani1.svg' %}">
                    <div class="tab3top_card tab4top_card">
                        <p class="textarea_label">Output Language<img src="./img/question_icon.svg"></p>
                        <div class="setting-options tab3_options" id="langOptions">
                            <label class="option">
                                <input type="radio" data-cost="{{ lang.cost }}" name="selected_language" value="{{ lang.id }}">
                                <span>🇬🇧 English</span>
                            </label>
                            <label class="option">
                                <input type="radio" data-cost="{{ lang.cost }}" name="selected_language" value="{{ lang.id }}">
                                <span>🇨🇳 Mandarin Chinese</span>
                            </label>
                            <label class="option">
                                <input type="radio" data-cost="{{ lang.cost }}" name="selected_language" value="{{ lang.id }}">
                                <span>🇫🇷 French</span>
                            </label>
                            <label class="option">
                                <input type="radio" data-cost="{{ lang.cost }}" name="selected_language" value="{{ lang.id }}">
                                <span>🇪🇸 Spanish</span>
                            </label>
                            <label class="option">
                                <input type="radio" data-cost="{{ lang.cost }}" name="selected_language" value="{{ lang.id }}">
                                <span>🇮🇳 Hindi</span>
                            </label>
                        </div>
                        <div class="custom-dropdown drop_btn2 other-dropdown">
                            <button class="dropdown-btn" id="otherLangBtn">
                                <span class="dropdown-text" id="otherLangText">Other</span>
                                <img src="./img/age_dropicon.svg" alt="Dropdown" class="dropdown-icon">
                            </button>
                            <ul class="dropdown-list" id="otherLangList">
                                <input type="hidden" id="selectedLangInput" name="selected_language">
                                <li>🇮🇳 Maharashtra</li>
                                <li>🇮🇳 Gujarat</li>
                                <li>🇮🇳 Punjab</li>
                                <li>🇮🇳 Odisha</li>
                            </ul>
                        </div>
                    </div>
                    <div class="tab4_mid">
                        <p class="textarea_label">Narrator Voice<img src="./img/question_icon.svg"></p>
                        <div class="speaker_main">
                            <div class="custom-dropdown lang-dropdown">
                                <button class="dropdown-btn" id="narratorBtn">
                                    <span class="dropdown-text" id="narratorText">Choose Narrator Voice</span>
                                    <img src="./img/age_dropicon.svg" alt="Dropdown" class="dropdown-icon">
                                </button>
                                <ul class="dropdown-list" id="narratorList">
                                    <li data-cost="0" data-value="" data-voice_url="" class="no-selection">English</li>
                                    <li data-cost="0" data-value="" data-voice_url="" class="no-selection">Hindi</li>
                                    <li data-cost="0" data-value="" data-voice_url="" class="no-selection">Marathi</li>
                                </ul>
                            </div>
                            <button class="speaker-btn speaker_btn" id="speakBtn"><img src="./img/speaker.svg" alt="Speak"></button>
                        </div>
                    </div>
                    <div class="char_btnbar">
                        <button type="button" class="btn char_btn1 back-btn" id="tab4Back">Back</button>
                        <button type="button" id="tab4Next" class="btn char_btn2" data-bs-toggle="modal" data-bs-target="#storyGenerationConfirmationModal">Create book (-100 tokens)</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Modal Start -->
<div class="modal fade" id="storyGenerationConfirmationModal" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content story_mcontent" style="min-height: 400px !important;">
            <div class="modal-body story_mbody">
                <div class="story_mtitlebar">
                    <h3 class="story_mtitle">Confirm token transaction</h3>
                    <p class="story_msubtitle">Creating your storybook costs <span id="show_total_tokens_on_modal" class="story_msubtitlebold">100 tokens.</span>Confirm to continue your adventure!</p>
                </div>
                <form class="story_mbtnbar"  method="POST" action="{% url 'story_book_create' %}" id="storyForm" onsubmit="return validateStoryForm()">
                    <button type="button" class="btn smodal_btn1 w-100" data-bs-dismiss="modal" aria-label="Close">Back</button>
                    <button type="submit" id="generate_story" class="btn smodal_btn2 w-100">Close</button>
                </form>
            </div>
        </div>
    </div>
</div>
<!-- Modal End -->

<?php include 'includes/footer.php'; ?>
<!-- JavaScript -->
 <script>
    document.addEventListener("DOMContentLoaded", () => {
        const staticDiamondYellow = "./img/diamond-glow.svg";
        const staticDiamondGlow = "./img/diamond-yellow.svg";
        const staticDiamondNormal = "./img/diamond-normal.svg";
        const totalTabs = 4;
        let currentTab = 0;
    
        function showTab(tabNumber) {
            if (tabNumber < 0 || tabNumber > totalTabs) return;
            currentTab = tabNumber;
    
            const storySection = document.getElementById('storySectionContainer');
            if (storySection) storySection.style.display = tabNumber > 0 ? 'block' : 'none';
    
            document.querySelectorAll('.tab-content').forEach(tab => tab.style.display = 'none');
            const currentTabEl = document.getElementById(tabNumber === 0 ? 'tab0' : `tab${tabNumber}`);
            if (currentTabEl) currentTabEl.style.display = 'block';
    
            const page = document.getElementById('storyPage');
            if (page && tabNumber > 0) {
                page.classList.forEach(cls => { if (cls.startsWith('bg-')) page.classList.remove(cls); });
                page.classList.add('bg-' + tabNumber);
            }
    
            for (let i = 1; i <= totalTabs; i++) {
                const diamond = document.getElementById(`diamond${i}`);
                const title = document.getElementById(`title${i}`);
                if (!diamond || !title) continue;
                diamond.classList.remove("glow-effect");
                if (i < tabNumber) {
                    diamond.src = staticDiamondYellow;
                    title.classList.remove("completed-title");
                } else if (i === tabNumber) {
                    diamond.src = staticDiamondGlow;
                    diamond.classList.add("glow-effect");
                    title.classList.add("completed-title");
                } else {
                    diamond.src = staticDiamondNormal;
                    title.classList.remove("completed-title");
                }
            }
    
            if (tabNumber > 0) scrollActiveStepToCenter(tabNumber);
            window.scrollTo({ top: 0, behavior: "smooth" });
        }
    
        function scrollActiveStepToCenter(tabNumber) {
            const progressBar = document.getElementById('progressBarMain');
            const diamondEl = document.getElementById(`diamond${tabNumber}`);
            const activeStep = diamondEl?.closest('.step');
            if (progressBar && activeStep) {
                const stepRect = activeStep.getBoundingClientRect();
                const containerRect = progressBar.getBoundingClientRect();
                const scrollLeft = progressBar.scrollLeft + (stepRect.left - containerRect.left) - (containerRect.width / 2) + (stepRect.width / 2);
                progressBar.scrollTo({ left: scrollLeft, behavior: 'smooth' });
            }
        }
    
        
    
        document.getElementById("tab0Next")?.addEventListener("click", async () => {
            if (true) {
                showTab(1);
            }
        });
    
        document.getElementById("tab1Next")?.addEventListener("click", async () => { showTab(2); });
        document.getElementById("tab2Next")?.addEventListener("click", async () => { showTab(3); });
        document.getElementById("tab3Next")?.addEventListener("click", async () => { showTab(4); });
    
        document.getElementById("tab4Next")?.addEventListener("click", async () => {
            const step4Response = await saveStepFour();
            if (!step4Response?.success) {
                window.notyf.open({ type: "error", message: step4Response?.error || "Failed to save step four." });
                return;
            }
    
            const storyData = step4Response.story_data;
            if (!storyData) {
                window.notyf.open({ type: "error", message: "Story data not found." });
                return;
            }
    
            const missingFields = [];
            if (!storyData.childgroup_id) missingFields.push("age group");
            if (!storyData.character_name) missingFields.push("character name");
            if (!storyData.character_desc) missingFields.push("character description");
            if (!storyData.setting_id) missingFields.push("setting");
            if (!storyData.plot_id) missingFields.push("plot");
            if (!storyData.theme_id) missingFields.push("theme");
            if (!storyData.imagestyle_id) missingFields.push("image style");
            if (!storyData.tone_id) missingFields.push("tone");
            if (!storyData.storylength_id) missingFields.push("story length");
            if (!storyData.language_id) missingFields.push("language");
    
            if (missingFields.length) {
                window.notyf.open({ type: "error", message: `Please complete: ${missingFields.join(", ")}` });
                return;
            }
    
            const modalEl = document.getElementById('storyGenerationConfirmationModal');
            if (modalEl) {
                const modal = new bootstrap.Modal(modalEl);
                modal.show();
            }
        });
    
        document.getElementById("tab1Back")?.addEventListener("click", () => showTab(0));
        document.getElementById("tab2Back")?.addEventListener("click", () => showTab(1));
        document.getElementById("tab3Back")?.addEventListener("click", () => showTab(2));
        document.getElementById("tab4Back")?.addEventListener("click", () => showTab(3));
    
        const textareas = [
            { textarea: "charLook", counter: "charLookCount" },
            { textarea: "settingTextarea", counter: "settingCount" },
            { textarea: "plotTextarea", counter: "plotCount" },
            { textarea: "themeTextarea", counter: "themeCount" }
        ];
    
        textareas.forEach(({ textarea, counter }) => {
            const ta = document.getElementById(textarea);
            const ct = document.getElementById(counter);
            if (!ta || !ct) return;
            const maxChars = parseInt(ta.getAttribute("maxlength"), 10);
            const updateCounter = () => {
                const length = ta.value.length;
                ct.textContent = `${length}/${maxChars}`;
                ct.style.color = length >= maxChars ? "#ff4444" : "var(--Core-Off-White, #FAFAFA)";
            };
            ta.addEventListener("input", updateCounter);
            new MutationObserver(updateCounter).observe(ta, { attributes: true, attributeFilter: ["style", "class"] });
            updateCounter();
        });
    
        const cardsContainer = document.getElementById("styleCardsContainer");
        if (cardsContainer) {
            cardsContainer.querySelectorAll('.card-item').forEach(card => {
                card.addEventListener('click', () => {
                    cardsContainer.querySelectorAll('.card-item').forEach(c => c.classList.remove('selected'));
                    card.classList.add('selected');
                    card.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
                });
            });
        }
    
        const dropdowns = document.querySelectorAll('.custom-dropdown');
        dropdowns.forEach(dropdown => {
            const button = dropdown.querySelector('.dropdown-btn');
            const list = dropdown.querySelector('.dropdown-list');
            const selectedText = dropdown.querySelector('.dropdown-text');

            if (!button || !list) return;

            // OPEN / CLOSE
            button.addEventListener('click', (e) => {
                e.stopPropagation();

                // close others
                dropdowns.forEach(d => {
                    if (d !== dropdown) d.classList.remove('open');
                });

                dropdown.classList.toggle('open');
            });

            // SELECT
            list.querySelectorAll('li').forEach(item => {
                item.addEventListener('click', (e) => {
                    e.stopPropagation();

                    list.querySelectorAll('li').forEach(li => li.classList.remove('selected'));
                    item.classList.add('selected');

                    selectedText.textContent = item.textContent;

                    dropdown.classList.remove('open');
                });
            });
        });

        // OUTSIDE CLICK CLOSE
        window.addEventListener('click', () => {
            document.querySelectorAll('.custom-dropdown').forEach(d => {
                d.classList.remove('open');
            });
        });

    
        const speakBtn = document.getElementById("speakBtn");
        const narratorBtn = document.getElementById("narratorBtn");
        const narratorText = document.getElementById("narratorText");
        if (speakBtn && narratorBtn && narratorText) {
            let currentAudio = null;
            document.querySelectorAll("#narratorList li").forEach(item => {
                item.addEventListener("click", () => {
                    narratorBtn.setAttribute("data-value", item.getAttribute("data-value"));
                    narratorBtn.setAttribute("data-voice_url", item.getAttribute("data-voice_url"));
                    narratorText.textContent = item.textContent;
                });
            });
    
            speakBtn.addEventListener("click", async () => {
                const voiceUrl = narratorBtn.getAttribute("data-voice_url");
                if (!voiceUrl) {
                    const utterance = new SpeechSynthesisUtterance("Please select a narrator.");
                    utterance.lang = "en-US";
                    utterance.rate = 0.9;
                    utterance.pitch = 1;
                    speechSynthesis.cancel();
                    speechSynthesis.speak(utterance);
                    return;
                }
    
                if (currentAudio) {
                    try { currentAudio.pause(); } catch(e) {}
                    currentAudio.currentTime = 0;
                }
    
                currentAudio = new Audio(voiceUrl);
                try { await currentAudio.play(); } catch(err) { if(err.name !== "AbortError") console.error(err); }
            });
        }
    
        const langRadios = document.querySelectorAll("input[name='main_language']");
        const langDropdownBtn = document.querySelector(".lang-dropdown .dropdown-btn");
        const langDropdownList = document.querySelector(".lang-dropdown .dropdown-list");
        if (langRadios && langDropdownBtn) {
            langRadios.forEach(radio => {
                radio.addEventListener("change", () => {
                    langDropdownBtn.setAttribute("data-value", "");
                    langDropdownBtn.querySelector(".dropdown-text").textContent = "Select Language";
                });
            });
    
            if (langDropdownList) {
                langDropdownList.querySelectorAll("li").forEach(item => {
                    item.addEventListener("click", () => {
                        langRadios.forEach(r => r.checked = false);
                    });
                });
            }
        }
    showTab(0);
    });
    
    function validateStoryForm() {
        const userBalance = Number("{{ request.user.profile.wallet|default:0 }}");
        const totalTokens = Number(document.getElementById("show_total_tokens_on_modal").textContent.replace(/\D/g,''));
    
        if (userBalance < totalTokens) {
            window.notyf.open({ type: "error", message: "You don't have enough tokens to generate this story." });
            return false;
        }
        const modalEl = document.getElementById("storyGenerationConfirmationModal");
        if (modalEl) {
            let modal = bootstrap.Modal.getInstance(modalEl);
            if (!modal) {
                modal = new bootstrap.Modal(modalEl);
            }
            modal.hide();
        }
        generationLoader(true,"Generating your story...");
        return true;
    }
</script>