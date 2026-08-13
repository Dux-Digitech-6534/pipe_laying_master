from cmr_pipe_laying_master.api.masters import get_master_options


def get_option_counts():
	options = get_master_options()
	return {key: len(value) for key, value in options.items()}
