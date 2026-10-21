/**
 * CLIPFLOW AI — FRONTEND APPLICATION LOGIC
 * High-performance YouTube to 9:16 Shorts Studio
 */

document.addEventListener("DOMContentLoaded", () => {
    // Initialize Lucide Icons
    if (window.lucide) {
        lucide.createIcons();
    }

    // State
    const state = {
        videoInfo: null,
        duration: 60,
        startSec: 0,
        endSec: 30,
        isPolling: false,
        pollingInterval: null
    };

    // DOM Elements
    const ytUrlInput = document.getElementById("yt-url-input");
    const inspectBtn = document.getElementById("inspect-btn");
    const pasteBtn = document.getElementById("paste-btn");
    const alertBanner = document.getElementById("alert-banner");
    const alertText = document.getElementById("alert-text");
    const demoPills = document.querySelectorAll(".demo-pill");

    const studioSection = document.getElementById("studio-section");
    const resultSection = document.getElementById("result-section");
    const processingModal = document.getElementById("processing-modal");

    // Meta elements
    const metaThumb = document.getElementById("meta-thumb");
    const metaTitle = document.getElementById("meta-title");
    const metaChannel = document.getElementById("meta-channel");
    const metaDuration = document.getElementById("meta-duration");
    const metaAspect = document.getElementById("meta-aspect");
    const changeVideoBtn = document.getElementById("change-video-btn");

    // Player & Timeline elements
    const playerWrapper = document.getElementById("yt-player-wrapper");
    const rangeStart = document.getElementById("range-start");
    const rangeEnd = document.getElementById("range-end");
    const sliderHighlight = document.getElementById("slider-highlight");
    const displayStartTime = document.getElementById("display-start-time");
    const displayEndTime = document.getElementById("display-end-time");
    const clipDurationBadge = document.getElementById("clip-duration-badge");
    const inputStartSec = document.getElementById("input-start-sec");
    const inputEndSec = document.getElementById("input-end-sec");
    const quickTrimBtns = document.querySelectorAll(".quick-trim-btn");

    // Customizer elements
    const styleCards = document.querySelectorAll(".style-card");
    const toggleHeadline = document.getElementById("toggle-headline");
    const headlineFields = document.getElementById("headline-fields");
    const headlineInput = document.getElementById("headline-input");
    const themeChips = document.querySelectorAll(".theme-chip");
    const toggleProgressBar = document.getElementById("toggle-progress-bar");
    const audioBoostSelect = document.getElementById("audio-boost-select");
    const watermarkInput = document.getElementById("watermark-input");
    const renderClipBtn = document.getElementById("render-clip-btn");

    // Progress Modal elements
    const progressFill = document.getElementById("progress-fill");
    const progressPct = document.getElementById("progress-pct");
    const progressStepText = document.getElementById("progress-step-text");
    const taskMessage = document.getElementById("task-message");
    const pipeSteps = {
        dl: document.getElementById("step-dl"),
        render: document.getElementById("step-render"),
        badge: document.getElementById("step-badge"),
        export: document.getElementById("step-export")
    };

    // Result elements
    const resultVideoPlayer = document.getElementById("result-video-player");
    const resClipTitle = document.getElementById("res-clip-title");
    const resBadgeStyle = document.getElementById("res-badge-style");
    const resDuration = document.getElementById("res-duration");
    const resResolution = document.getElementById("res-resolution");
    const resFilesize = document.getElementById("res-filesize");
    const btnDownloadClip = document.getElementById("btn-download-clip");
    const btnCopyLink = document.getElementById("btn-copy-link");
    const btnTrimAnother = document.getElementById("btn-trim-another");
    const btnCreateNew = document.getElementById("btn-create-new");

    // Gallery elements
    const clipsGrid = document.getElementById("clips-grid");
    const galleryCount = document.getElementById("gallery-count");
    const galleryEmptyState = document.getElementById("gallery-empty-state");

    // Preview Modal elements
    const previewModal = document.getElementById("preview-modal");
    const modalVideo = document.getElementById("modal-video");
    const modalVideoTitle = document.getElementById("modal-video-title");
    const modalVideoDownload = document.getElementById("modal-video-download");
    const closePreviewModal = document.getElementById("close-preview-modal");

    // --- Helper Functions ---
    function formatTime(seconds) {
        if (isNaN(seconds) || seconds === null) return "00:00.0";
        const total = Math.max(0, Number(seconds));
        const mins = Math.floor(total / 60);
        const secs = (total % 60).toFixed(1);
        const sStr = secs < 10 ? "0" + secs : secs;
        const mStr = mins < 10 ? "0" + mins : mins;
        return `${mStr}:${sStr}`;
    }

    function showAlert(msg) {
        alertText.textContent = msg;
        alertBanner.classList.remove("hidden");
        if (window.lucide) lucide.createIcons();
    }

    function hideAlert() {
        alertBanner.classList.add("hidden");
    }

    // --- Paste from Clipboard ---
    if (pasteBtn) {
        pasteBtn.addEventListener("click", async () => {
            try {
                const text = await navigator.clipboard.readText();
                if (text) {
                    ytUrlInput.value = text.trim();
                    handleInspectVideo();
                }
            } catch (err) {
                showAlert("Please allow clipboard permissions or paste manually.");
            }
        });
    }

    // --- Demo Pills ---
    demoPills.forEach(pill => {
        pill.addEventListener("click", () => {
            const url = pill.getAttribute("data-url");
            if (url) {
                ytUrlInput.value = url;
                handleInspectVideo();
            }
        });
    });

    // --- Inspect Video ---
    inspectBtn.addEventListener("click", handleInspectVideo);
    ytUrlInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") handleInspectVideo();
    });

    async function handleInspectVideo() {
        const url = ytUrlInput.value.trim();
        if (!url) {
            showAlert("Please enter a valid YouTube video or shorts link.");
            return;
        }

        hideAlert();
        inspectBtn.disabled = true;
        inspectBtn.innerHTML = `<span class="btn-text">Inspecting...</span><i data-lucide="loader-2" class="icon-spin"></i>`;
        if (window.lucide) lucide.createIcons();

        try {
            const res = await fetch("/api/info", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Unable to inspect video.");
            }

            const data = await res.json();
            state.videoInfo = data;
            state.duration = data.duration > 0 ? data.duration : 60;
            state.startSec = 0;
            state.endSec = Math.min(30, state.duration);

            setupStudioWithVideo(data);
        } catch (err) {
            console.error(err);
            showAlert(err.message || "Failed to inspect video. Please check the URL.");
        } finally {
            inspectBtn.disabled = false;
            inspectBtn.innerHTML = `<span class="btn-text">Inspect Video</span><i data-lucide="arrow-right"></i>`;
            if (window.lucide) lucide.createIcons();
        }
    }

    function setupStudioWithVideo(info) {
        // Populate Meta
        metaTitle.textContent = info.title;
        metaChannel.innerHTML = `<i data-lucide="user"></i> ${info.uploader || info.channel}`;
        metaDuration.innerHTML = `<i data-lucide="clock"></i> ${info.duration_formatted}`;
        metaThumb.src = info.thumbnail;

        if (info.is_vertical) {
            metaAspect.innerHTML = `<i data-lucide="smartphone"></i> 9:16 Vertical Short`;
            metaAspect.className = "meta-tag badge-cyan";
            // Preselect Original style if already vertical
            selectStyleCard("original");
        } else {
            metaAspect.innerHTML = `<i data-lucide="monitor"></i> ${info.width}x${info.height} (16:9)`;
            metaAspect.className = "meta-tag";
            selectStyleCard("blur_9_16");
        }

        // Embed YouTube Player
        const embedUrl = `https://www.youtube-nocookie.com/embed/${info.id}?rel=0&modestbranding=1&enablejsapi=1`;
        playerWrapper.innerHTML = `
            <iframe 
                src="${embedUrl}" 
                title="${info.title}" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen>
            </iframe>
        `;

        // Update Slider ranges
        rangeStart.min = 0;
        rangeStart.max = state.duration;
        rangeStart.value = 0;

        rangeEnd.min = 0;
        rangeEnd.max = state.duration;
        rangeEnd.value = state.endSec;

        inputStartSec.max = state.duration;
        inputEndSec.max = state.duration;

        updateTimelineUI();

        // Reveal Studio
        studioSection.classList.remove("hidden");
        studioSection.scrollIntoView({ behavior: "smooth", block: "start" });
        if (window.lucide) lucide.createIcons();
    }

    // --- Style Cards Selection ---
    function selectStyleCard(value) {
        styleCards.forEach(card => {
            const radio = card.querySelector("input[type='radio']");
            if (radio.value === value) {
                radio.checked = true;
                card.classList.add("selected");
            } else {
                card.classList.remove("selected");
            }
        });
    }

    styleCards.forEach(card => {
        card.addEventListener("click", () => {
            styleCards.forEach(c => c.classList.remove("selected"));
            card.classList.add("selected");
            const radio = card.querySelector("input[type='radio']");
            if (radio) radio.checked = true;
        });
    });

    // --- Headline Toggle & Themes ---
    if (toggleHeadline) {
        toggleHeadline.addEventListener("change", () => {
            if (toggleHeadline.checked) {
                headlineFields.style.opacity = "1";
                headlineFields.style.pointerEvents = "auto";
            } else {
                headlineFields.style.opacity = "0.35";
                headlineFields.style.pointerEvents = "none";
            }
        });
    }

    themeChips.forEach(chip => {
        chip.addEventListener("click", () => {
            themeChips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            const radio = chip.querySelector("input[type='radio']");
            if (radio) radio.checked = true;
        });
    });

    // --- Timeline Dual Slider Mechanics ---
    function updateTimelineUI() {
        const s = parseFloat(rangeStart.value);
        const e = parseFloat(rangeEnd.value);
        state.startSec = s;
        state.endSec = e;

        // Position highlight bar
        const total = state.duration || 100;
        const leftPct = (s / total) * 100;
        const widthPct = ((e - s) / total) * 100;
        sliderHighlight.style.left = `${leftPct}%`;
        sliderHighlight.style.width = `${widthPct}%`;

        // Update readouts
        displayStartTime.textContent = formatTime(s);
        displayEndTime.textContent = formatTime(e);
        const clipLen = Math.max(0, e - s);
        clipDurationBadge.textContent = `${formatTime(clipLen)} (${clipLen.toFixed(1)}s)`;

        // Sync inputs
        inputStartSec.value = s.toFixed(1);
        inputEndSec.value = e.toFixed(1);
    }

    rangeStart.addEventListener("input", () => {
        let s = parseFloat(rangeStart.value);
        let e = parseFloat(rangeEnd.value);
        if (s >= e - 1.0) {
            s = Math.max(0, e - 1.0);
            rangeStart.value = s;
        }
        updateTimelineUI();
    });

    rangeEnd.addEventListener("input", () => {
        let s = parseFloat(rangeStart.value);
        let e = parseFloat(rangeEnd.value);
        if (e <= s + 1.0) {
            e = Math.min(state.duration, s + 1.0);
            rangeEnd.value = e;
        }
        updateTimelineUI();
    });

    // Manual Steppers
    document.getElementById("btn-step-start-down")?.addEventListener("click", () => {
        rangeStart.value = Math.max(0, parseFloat(rangeStart.value) - 1.0);
        updateTimelineUI();
    });
    document.getElementById("btn-step-start-up")?.addEventListener("click", () => {
        rangeStart.value = Math.min(parseFloat(rangeEnd.value) - 1.0, parseFloat(rangeStart.value) + 1.0);
        updateTimelineUI();
    });
    document.getElementById("btn-step-end-down")?.addEventListener("click", () => {
        rangeEnd.value = Math.max(parseFloat(rangeStart.value) + 1.0, parseFloat(rangeEnd.value) - 1.0);
        updateTimelineUI();
    });
    document.getElementById("btn-step-end-up")?.addEventListener("click", () => {
        rangeEnd.value = Math.min(state.duration, parseFloat(rangeEnd.value) + 1.0);
        updateTimelineUI();
    });

    inputStartSec.addEventListener("change", () => {
        let val = Math.max(0, Math.min(state.duration - 1, parseFloat(inputStartSec.value) || 0));
        if (val >= state.endSec) val = state.endSec - 1;
        rangeStart.value = val;
        updateTimelineUI();
    });

    inputEndSec.addEventListener("change", () => {
        let val = Math.max(state.startSec + 1, Math.min(state.duration, parseFloat(inputEndSec.value) || 10));
        rangeEnd.value = val;
        updateTimelineUI();
    });

    // Quick Trim Buttons (15s, 30s, 60s)
    quickTrimBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            quickTrimBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const targetDur = parseFloat(btn.getAttribute("data-dur"));
            let newEnd = state.startSec + targetDur;
            if (newEnd > state.duration) {
                newEnd = state.duration;
                state.startSec = Math.max(0, newEnd - targetDur);
                rangeStart.value = state.startSec;
            }
            rangeEnd.value = newEnd;
            updateTimelineUI();
        });
    });

    // --- Render Clip Action ---
    renderClipBtn.addEventListener("click", async () => {
        if (!state.videoInfo) {
            showAlert("Please inspect a YouTube video first.");
            return;
        }

        const selectedStyleRadio = document.querySelector("input[name='clip_style']:checked");
        const style = selectedStyleRadio ? selectedStyleRadio.value : "blur_9_16";

        const hasHeadline = toggleHeadline && toggleHeadline.checked;
        const headlineText = hasHeadline ? headlineInput.value.trim() : null;

        const selectedHlRadio = document.querySelector("input[name='hl_style']:checked");
        const headlineStyle = selectedHlRadio ? selectedHlRadio.value : "yellow";

        const hasProgressBar = toggleProgressBar && toggleProgressBar.checked;
        const audioBoost = parseFloat(audioBoostSelect.value || "1.0");
        const watermark = watermarkInput.value.trim() || null;

        const payload = {
            url: state.videoInfo.webpage_url,
            start_sec: state.startSec,
            end_sec: state.endSec,
            style: style,
            headline_text: headlineText,
            headline_style: headlineStyle,
            progress_bar: hasProgressBar,
            watermark: watermark,
            audio_boost: audioBoost,
            title: state.videoInfo.title,
            thumbnail: state.videoInfo.thumbnail
        };

        // Open Processing Modal
        openProcessingModal();

        try {
            const res = await fetch("/api/clip", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Failed to start clip rendering.");
            }

            const data = await res.json();
            startTaskPolling(data.task_id);
        } catch (err) {
            console.error(err);
            closeProcessingModal();
            showAlert(err.message || "Failed to start clipping task.");
        }
    });

    function openProcessingModal() {
        processingModal.classList.remove("hidden");
        updateModalProgress(10, "Extracting video stream from YouTube...", "dl");
    }

    function closeProcessingModal() {
        processingModal.classList.add("hidden");
        if (state.pollingInterval) {
            clearInterval(state.pollingInterval);
            state.pollingInterval = null;
        }
    }

    function updateModalProgress(pct, message, activeStepKey) {
        progressFill.style.width = `${pct}%`;
        progressPct.textContent = `${pct}%`;
        taskMessage.textContent = message;
        progressStepText.textContent = message;

        const stepOrder = ["dl", "render", "badge", "export"];
        const activeIdx = stepOrder.indexOf(activeStepKey);

        stepOrder.forEach((key, idx) => {
            const el = pipeSteps[key];
            if (!el) return;
            if (idx < activeIdx) {
                el.className = "pipe-step done";
            } else if (idx === activeIdx) {
                el.className = "pipe-step active";
            } else {
                el.className = "pipe-step";
            }
        });
    }

    function startTaskPolling(taskId) {
        if (state.pollingInterval) clearInterval(state.pollingInterval);

        state.pollingInterval = setInterval(async () => {
            try {
                const res = await fetch(`/api/status/${taskId}`);
                if (!res.ok) return;

                const data = await res.json();
                const prog = data.progress || 10;
                let stepKey = "dl";
                if (prog >= 75) stepKey = "export";
                else if (prog >= 50) stepKey = "badge";
                else if (prog >= 30) stepKey = "render";

                updateModalProgress(prog, data.message || "Processing...", stepKey);

                if (data.status === "completed" && data.result) {
                    clearInterval(state.pollingInterval);
                    state.pollingInterval = null;
                    setTimeout(() => {
                        closeProcessingModal();
                        displayRenderResult(data.result);
                        loadClipsGallery();
                    }, 600);
                } else if (data.status === "failed") {
                    clearInterval(state.pollingInterval);
                    state.pollingInterval = null;
                    closeProcessingModal();
                    showAlert(`Generation failed: ${data.error || "Unknown error"}`);
                }
            } catch (e) {
                console.error("Polling error:", e);
            }
        }, 1000);
    }

    // --- Display Result in Smartphone Mockup ---
    function displayRenderResult(result) {
        resClipTitle.textContent = result.title;
        resBadgeStyle.textContent = result.style.replace("_", " ").toUpperCase();
        resDuration.textContent = `${result.duration_formatted} (${result.duration.toFixed(1)}s)`;
        resResolution.textContent = `${result.width} × ${result.height}`;
        resFilesize.textContent = `${result.file_size_mb} MB`;

        btnDownloadClip.href = result.download_url;
        btnDownloadClip.setAttribute("download", result.filename);

        // Load into mock player
        resultVideoPlayer.src = result.stream_url;
        resultVideoPlayer.load();
        resultVideoPlayer.play().catch(() => {});

        // Copy direct link
        btnCopyLink.onclick = () => {
            const fullUrl = window.location.origin + result.stream_url;
            navigator.clipboard.writeText(fullUrl).then(() => {
                btnCopyLink.innerHTML = `<i data-lucide="check"></i> Copied!`;
                if (window.lucide) lucide.createIcons();
                setTimeout(() => {
                    btnCopyLink.innerHTML = `<i data-lucide="copy"></i> Copy Video Link`;
                    if (window.lucide) lucide.createIcons();
                }, 2000);
            });
        };

        resultSection.classList.remove("hidden");
        resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
        if (window.lucide) lucide.createIcons();
    }

    // Buttons in result view
    if (btnTrimAnother) {
        btnTrimAnother.addEventListener("click", () => {
            studioSection.scrollIntoView({ behavior: "smooth", block: "start" });
        });
    }

    if (btnCreateNew) {
        btnCreateNew.addEventListener("click", () => {
            ytUrlInput.value = "";
            ytUrlInput.focus();
            window.scrollTo({ top: 0, behavior: "smooth" });
        });
    }

    if (changeVideoBtn) {
        changeVideoBtn.addEventListener("click", () => {
            ytUrlInput.value = "";
            ytUrlInput.focus();
            window.scrollTo({ top: 0, behavior: "smooth" });
        });
    }

    // --- Clips Gallery Management ---
    async function loadClipsGallery() {
        try {
            const res = await fetch("/api/clips");
            if (!res.ok) return;

            const data = await res.json();
            const clips = data.clips || [];

            galleryCount.textContent = clips.length;

            if (clips.length === 0) {
                galleryEmptyState.classList.remove("hidden");
                // Remove all other cards
                const existingCards = clipsGrid.querySelectorAll(".clip-card");
                existingCards.forEach(c => c.remove());
                return;
            }

            galleryEmptyState.classList.add("hidden");
            // Clear existing cards
            const existingCards = clipsGrid.querySelectorAll(".clip-card");
            existingCards.forEach(c => c.remove());

            clips.forEach(clip => {
                const card = document.createElement("div");
                card.className = "clip-card";
                card.innerHTML = `
                    <div class="clip-card-thumb-wrapper" data-stream="${clip.stream_url}" data-title="${clip.title.replace(/"/g, '&quot;')}">
                        <video src="${clip.stream_url}#t=0.5" preload="metadata" muted playsinline></video>
                        <span class="clip-card-duration">${clip.duration_formatted}</span>
                    </div>
                    <div class="clip-card-body">
                        <div>
                            <h4 class="clip-card-title">${clip.title}</h4>
                            <div class="clip-card-meta">
                                <span>${clip.file_size_mb} MB • ${clip.created_at_formatted || 'Recent'}</span>
                                <span class="info-pill">${clip.style.split('_')[0].toUpperCase()}</span>
                            </div>
                        </div>
                        <div class="clip-card-actions">
                            <a href="${clip.download_url}" download="${clip.filename}" class="btn-primary btn-sm" style="flex:1; justify-content:center;">
                                <i data-lucide="download"></i> Download
                            </a>
                            <button class="btn-secondary btn-sm delete-clip-btn" data-file="${clip.filename}" title="Delete clip">
                                <i data-lucide="trash-2"></i>
                            </button>
                        </div>
                    </div>
                `;

                // Card thumbnail click opens preview modal
                const thumb = card.querySelector(".clip-card-thumb-wrapper");
                thumb.addEventListener("click", () => {
                    openVideoModal(clip.stream_url, clip.title, clip.download_url, clip.filename);
                });

                // Delete button
                const delBtn = card.querySelector(".delete-clip-btn");
                delBtn.addEventListener("click", async (e) => {
                    e.stopPropagation();
                    if (confirm("Delete this clip from gallery?")) {
                        await fetch(`/api/clips/${clip.filename}`, { method: "DELETE" });
                        loadClipsGallery();
                    }
                });

                clipsGrid.appendChild(card);
            });

            if (window.lucide) lucide.createIcons();
        } catch (e) {
            console.error("Failed to load clips gallery:", e);
        }
    }

    function openVideoModal(streamUrl, title, downloadUrl, filename) {
        modalVideo.src = streamUrl;
        modalVideoTitle.textContent = title;
        modalVideoDownload.href = downloadUrl;
        modalVideoDownload.setAttribute("download", filename);
        previewModal.classList.remove("hidden");
        modalVideo.play().catch(() => {});
        if (window.lucide) lucide.createIcons();
    }

    if (closePreviewModal) {
        closePreviewModal.addEventListener("click", () => {
            modalVideo.pause();
            modalVideo.src = "";
            previewModal.classList.add("hidden");
        });
    }

    previewModal.addEventListener("click", (e) => {
        if (e.target === previewModal) {
            modalVideo.pause();
            modalVideo.src = "";
            previewModal.classList.add("hidden");
        }
    });

    // Check system health on launch
    async function checkSystemHealth() {
        try {
            const res = await fetch("/api/health");
            if (res.ok) {
                const data = await res.json();
                const indicator = document.getElementById("system-status-indicator");
                if (data.ffmpeg && data.node && data.yt_dlp) {
                    indicator.innerHTML = `<span class="status-dot"></span><span class="status-label">Engine Ready</span>`;
                    indicator.title = `FFmpeg: ${data.ffmpeg_path}\nNode: ${data.node_path}\nyt-dlp: ${data.yt_dlp_path}`;
                } else {
                    indicator.innerHTML = `<span class="status-dot" style="background:#f59e0b; box-shadow:0 0 10px #f59e0b;"></span><span class="status-label" style="color:#fbbf24;">Engine Warning</span>`;
                }
            }
        } catch (e) {
            console.error(e);
        }
    }

    // Initial loads
    checkSystemHealth();
    loadClipsGallery();
});
