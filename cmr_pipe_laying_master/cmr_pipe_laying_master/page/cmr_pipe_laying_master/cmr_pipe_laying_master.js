frappe.pages["cmr-pipe-laying-master"].on_page_load = function (wrapper) {
	const UI_VERSION = "12";
	const page = frappe.ui.make_app_page({ parent: wrapper, title: __("CMR Pipe Laying Master"), single_column: true });
	$(wrapper).find(".page-head").hide();
	page.main.html('<div class="cmr-page-host"><div class="cmr-loading">Loading CMR Pipe Laying Master...</div></div>');
	const host = page.main.find(".cmr-page-host").get(0);

	function show_error(message) {
		host.innerHTML = '<div class="cmr-load-error"><b>CMR application could not be loaded.</b><span>' + frappe.utils.escape_html(message) + '</span><button type="button" onclick="window.location.reload()">Retry</button></div>';
	}

	function remove_stale_assets() {
		if (window.CMRPipeLayingMaster?.version === UI_VERSION) return;
		if (window.CMRPipeLayingMaster?.unmount) {
			try { window.CMRPipeLayingMaster.unmount(); } catch (error) { /* stale app already detached */ }
		}
		delete window.CMRPipeLayingMaster;
		document.querySelectorAll('script[data-cmr-ui], link[data-cmr-ui]').forEach((element) => element.remove());
	}

	function load_css(url) {
		const current = document.querySelector(`link[data-cmr-ui="${UI_VERSION}"]`);
		if (current) return;
		const link = document.createElement("link");
		link.rel = "stylesheet";
		link.href = `${url}?v=${UI_VERSION}`;
		link.dataset.cmrUi = UI_VERSION;
		document.head.appendChild(link);
	}

	function load_script(url) {
		return new Promise((resolve, reject) => {
			if (window.CMRPipeLayingMaster?.version === UI_VERSION) return resolve();
			document.querySelectorAll('script[data-cmr-ui]').forEach((element) => element.remove());
			const script = document.createElement("script");
			script.src = `${url}?v=${UI_VERSION}`;
			script.async = true;
			script.dataset.cmrUi = UI_VERSION;
			script.onload = resolve;
			script.onerror = () => reject(new Error("CMR frontend JavaScript could not be downloaded."));
			document.head.appendChild(script);
		});
	}

	remove_stale_assets();
	frappe.call({
		method: "cmr_pipe_laying_master.api.bootstrap.get_bootstrap",
		callback: async function (response) {
			try {
				load_css("/assets/cmr_pipe_laying_master/dist/cmr-pipe-laying-master-v12.css");
				await load_script("/assets/cmr_pipe_laying_master/dist/cmr-pipe-laying-master-v12.js");
				if (!window.CMRPipeLayingMaster?.mount || window.CMRPipeLayingMaster.version !== UI_VERSION) throw new Error("Latest frontend bundle could not be activated.");
				window.CMRPipeLayingMaster.mount(host, { bootstrap: response.message || {} });
			} catch (error) {
				show_error(error.message || "Unknown frontend error");
			}
		},
		error: function () { show_error("Bootstrap data request failed."); },
	});
};

frappe.pages["cmr-pipe-laying-master"].on_page_hide = function () {
	if (window.CMRPipeLayingMaster?.unmount) window.CMRPipeLayingMaster.unmount();
};