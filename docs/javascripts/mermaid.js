/* ---------------------------------------------------------------------------
 * Mermaid 渲染 + 缩放 / 平移
 *
 * 背景：Material for MkDocs（9.7.x）内置的 Mermaid 集成在本项目的版本组合下
 *       只会清空占位元素、没有填回 SVG，导致图表整体不显示；它也没有提供
 *       任何缩放手段，宽图上的文字小到无法阅读。
 *
 * 所以这里改为自行渲染，并补上缩放/平移：
 *   · 自管 Mermaid 渲染（库由 mkdocs.yml 的 extra_javascript 本地引入，不依赖 CDN）
 *   · 滚轮缩放（以光标位置为中心）
 *   · 按住拖动平移
 *   · 双击重置
 *   · 工具栏：缩小 / 适应宽度 / 原始大小 / 放大
 *
 * 依赖：custom_fences 的 class 必须是 mermaid-diagram（见 mkdocs.yml），
 *       这样才能避开 Material 自己的处理流程。
 * ------------------------------------------------------------------------- */
(function () {
  "use strict";

  if (window.__mzLoaded) return;
  window.__mzLoaded = true;

  var SELECTOR = ".mermaid-diagram";
  // 手动缩放的下限 / 上限
  var MIN_SCALE = 0.1;
  var MAX_SCALE = 16;
  // 「适应宽度」允许比手动下限更小，否则超宽图无法一次看全
  var FIT_FLOOR = 0.02;
  var STEP = 1.25;

  var renderSeq = 0;
  var mermaidReady = false;

  function clamp(value, lo, hi) {
    return value < lo ? lo : value > hi ? hi : value;
  }

  /* =============================== 渲染 =============================== */

  function ensureMermaid() {
    if (mermaidReady) return true;
    if (!window.mermaid || typeof window.mermaid.render !== "function") {
      return false;
    }
    window.mermaid.initialize({
      startOnLoad: false,
      securityLevel: "loose",
      theme: "default",
      // 关掉 useMaxWidth，让 SVG 保留自然尺寸，缩放交给 CSS transform
      flowchart: { useMaxWidth: false },
      sequence: { useMaxWidth: false },
      gantt: { useMaxWidth: false }
    });
    mermaidReady = true;
    return true;
  }

  function paint(node, source) {
    var id = "mz-diagram-" + (++renderSeq);
    window.mermaid
      .render(id, source)
      .then(function (result) {
        node.innerHTML = result.svg;
        node.setAttribute("data-mz-state", "ready");
        enhance(node);
      })
      .catch(function (error) {
        // 渲染失败时回退显示源码，避免页面出现一片空白
        node.setAttribute("data-mz-state", "error");
        node.textContent = source;
        if (window.console) {
          console.error("[mermaid] 渲染失败：", error);
        }
      });
  }

  function renderAll() {
    if (!ensureMermaid()) return;
    var nodes = document.querySelectorAll(SELECTOR);
    for (var i = 0; i < nodes.length; i++) {
      var node = nodes[i];
      var state = node.getAttribute("data-mz-state");
      if (state === "ready" || state === "pending") continue;

      var source = node.getAttribute("data-mz-src") || node.textContent;
      if (!source || !source.trim()) continue;

      node.setAttribute("data-mz-src", source);
      node.setAttribute("data-mz-state", "pending");
      paint(node, source);
    }
  }

  /* =========================== 缩放 / 平移 =========================== */

  function enhance(container) {
    if (container.getAttribute("data-mz-ready") === "1") return;

    var svg = container.querySelector("svg");
    if (!svg) return;
    container.setAttribute("data-mz-ready", "1");

    /* ------------------------------ 布局 ------------------------------ */
    var wrapper = document.createElement("div");
    wrapper.className = "mz-wrapper";

    var stage = document.createElement("div");
    stage.className = "mz-stage";

    container.parentNode.insertBefore(wrapper, container);
    stage.appendChild(container);
    wrapper.appendChild(stage);

    var bar = document.createElement("div");
    bar.className = "mz-bar";
    bar.innerHTML =
      '<button type="button" data-act="out" title="缩小" aria-label="缩小">−</button>' +
      '<button type="button" data-act="fit" title="适应宽度" aria-label="适应宽度">适应</button>' +
      '<button type="button" data-act="one" title="原始大小" aria-label="原始大小">1:1</button>' +
      '<button type="button" data-act="in" title="放大" aria-label="放大">+</button>';
    wrapper.appendChild(bar);

    /* --------------------------- 自然尺寸 --------------------------- */
    var viewBox = svg.viewBox && svg.viewBox.baseVal;
    var naturalWidth =
      viewBox && viewBox.width
        ? viewBox.width
        : svg.getBoundingClientRect().width;

    svg.style.maxWidth = "none";
    svg.style.width = naturalWidth + "px";
    svg.style.height = "auto";
    svg.style.transformOrigin = "0 0";

    /* ------------------------------ 状态 ------------------------------ */
    var scale = 1;
    var offsetX = 0;
    var offsetY = 0;

    function apply() {
      svg.style.transform =
        "translate(" + offsetX + "px, " + offsetY + "px) scale(" + scale + ")";
    }

    function zoomAt(factor, anchorX, anchorY) {
      var next = clamp(scale * factor, MIN_SCALE, MAX_SCALE);
      var ratio = next / scale;
      offsetX = anchorX - ratio * (anchorX - offsetX);
      offsetY = anchorY - ratio * (anchorY - offsetY);
      scale = next;
      apply();
    }

    function reset() {
      scale = 1;
      offsetX = 0;
      offsetY = 0;
      apply();
    }

    function fitWidth() {
      var style = window.getComputedStyle(stage);
      var padding =
        parseFloat(style.paddingLeft || 0) + parseFloat(style.paddingRight || 0);
      var available = stage.clientWidth - padding;
      if (!naturalWidth || available <= 0) return;
      // 只缩小、不放大：图比容器窄时保持原始大小
      scale = clamp(Math.min(1, available / naturalWidth), FIT_FLOOR, MAX_SCALE);
      offsetX = 0;
      offsetY = 0;
      apply();
    }

    function zoomFromCenter(factor) {
      var rect = stage.getBoundingClientRect();
      zoomAt(factor, rect.width / 2, rect.height / 2);
    }

    /* ------------------- 滚轮缩放（以光标为中心） ------------------- */
    stage.addEventListener(
      "wheel",
      function (event) {
        event.preventDefault();
        var rect = stage.getBoundingClientRect();
        zoomAt(
          event.deltaY < 0 ? STEP : 1 / STEP,
          event.clientX - rect.left,
          event.clientY - rect.top
        );
      },
      { passive: false }
    );

    /* ----------------------------- 拖动平移 ----------------------------- */
    var dragging = false;
    var startX = 0;
    var startY = 0;
    var startOffsetX = 0;
    var startOffsetY = 0;

    stage.addEventListener("pointerdown", function (event) {
      if (event.pointerType === "mouse" && event.button !== 0) return;
      dragging = true;
      startX = event.clientX;
      startY = event.clientY;
      startOffsetX = offsetX;
      startOffsetY = offsetY;
      stage.classList.add("mz-dragging");
      if (stage.setPointerCapture) {
        try {
          stage.setPointerCapture(event.pointerId);
        } catch (err) {
          /* 捕获失败不影响基本拖动 */
        }
      }
    });

    stage.addEventListener("pointermove", function (event) {
      if (!dragging) return;
      offsetX = startOffsetX + (event.clientX - startX);
      offsetY = startOffsetY + (event.clientY - startY);
      apply();
    });

    function endDrag(event) {
      if (!dragging) return;
      dragging = false;
      stage.classList.remove("mz-dragging");
      if (stage.releasePointerCapture && event.pointerId !== undefined) {
        try {
          stage.releasePointerCapture(event.pointerId);
        } catch (err) {
          /* 已释放则忽略 */
        }
      }
    }

    stage.addEventListener("pointerup", endDrag);
    stage.addEventListener("pointercancel", endDrag);

    /* ----------------------------- 双击重置 ----------------------------- */
    stage.addEventListener("dblclick", reset);

    /* ------------------------------ 工具栏 ------------------------------ */
    bar.addEventListener("click", function (event) {
      var target = event.target;
      var button =
        target && target.closest ? target.closest("button[data-act]") : null;
      if (!button) return;

      var action = button.getAttribute("data-act");
      if (action === "in") zoomFromCenter(STEP);
      else if (action === "out") zoomFromCenter(1 / STEP);
      else if (action === "fit") fitWidth();
      else if (action === "one") reset();
    });

    // 初始状态：能完整看到全图
    fitWidth();
  }

  /* =============================== 启动 =============================== */

  var observer = null;
  var scheduled = false;

  function watch() {
    if (observer) observer.disconnect();
    observer = new MutationObserver(function () {
      if (scheduled) return;
      scheduled = true;
      window.requestAnimationFrame(function () {
        scheduled = false;
        renderAll();
      });
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }

  function boot() {
    renderAll();
    watch();
  }

  function start() {
    if (ensureMermaid()) {
      boot();
      return;
    }
    // Mermaid 库与脚本同为同步 <script>，通常已就绪；
    // 若因网络或顺序问题尚未加载，轮询等待最多 10 秒。
    var tries = 0;
    var timer = window.setInterval(function () {
      tries += 1;
      if (ensureMermaid() || tries > 100) {
        window.clearInterval(timer);
        if (window.mermaid) boot();
      }
    }, 100);
  }

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(start);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
