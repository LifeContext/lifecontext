// Page Context JS：运行在页面环境，负责把按钮点击通过 postMessage 传递给内容脚本
(function () {
  try {
    if (window.__LC_BRIDGE__) return;
    window.__LC_BRIDGE__ = true;
    document.addEventListener(
      'click',
      function (ev) {
        try {
          var t = ev.target;
          var btn = t && t.closest ? t.closest('#lc-optimize-btn-inline') : null;
          if (btn) {
            window.postMessage({ source: 'lc-page', type: 'LC_OPTIMIZE_CLICK' }, '*');
            ev.preventDefault();
            ev.stopPropagation();
          }
        } catch (e) {}
      },
      true
    );
  } catch (e) {}
})(); 


