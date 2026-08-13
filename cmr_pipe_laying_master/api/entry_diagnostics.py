from cmr_pipe_laying_master.api.entries import get_entry_options


def get_option_counts():
	options = get_entry_options()
	return {key: len(value) for key, value in options.items()}
