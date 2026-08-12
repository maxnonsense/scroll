#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include "sway/commands.h"
#include "stringop.h"

static int parse_corner(const char *name) {
	if (strcasecmp(name, "top_left") == 0 || strcasecmp(name, "top-left") == 0 ||
			strcasecmp(name, "topleft") == 0) {
		return HOT_CORNER_TOP_LEFT;
	}
	if (strcasecmp(name, "top_right") == 0 || strcasecmp(name, "top-right") == 0 ||
			strcasecmp(name, "topright") == 0) {
		return HOT_CORNER_TOP_RIGHT;
	}
	if (strcasecmp(name, "bottom_right") == 0 || strcasecmp(name, "bottom-right") == 0 ||
			strcasecmp(name, "bottomright") == 0) {
		return HOT_CORNER_BOTTOM_RIGHT;
	}
	if (strcasecmp(name, "bottom_left") == 0 || strcasecmp(name, "bottom-left") == 0 ||
			strcasecmp(name, "bottomleft") == 0) {
		return HOT_CORNER_BOTTOM_LEFT;
	}
	return -1;
}

struct cmd_results *cmd_hot_corner(int argc, char **argv) {
	struct cmd_results *error;
	if ((error = checkarg(argc, "hot_corner", EXPECTED_AT_LEAST, 2))) {
		return error;
	}
	int corner = parse_corner(argv[0]);
	if (corner < 0) {
		return cmd_results_new(CMD_INVALID,
			"Expected 'hot_corner <top_left|top_right|bottom_left|bottom_right> <command|none>'");
	}
	char *command = join_args(argv + 1, argc - 1);
	free(config->hot_corners[corner]);
	if (strcasecmp(command, "none") == 0 || strcasecmp(command, "disable") == 0) {
		free(command);
		config->hot_corners[corner] = NULL;
	} else {
		config->hot_corners[corner] = command;
	}
	return cmd_results_new(CMD_SUCCESS, NULL);
}

struct cmd_results *cmd_hot_corner_size(int argc, char **argv) {
	struct cmd_results *error;
	if ((error = checkarg(argc, "hot_corner_size", EXPECTED_AT_LEAST, 1))) {
		return error;
	}
	char *inv;
	int value = strtol(argv[0], &inv, 10);
	if (*inv != '\0' || value < 1) {
		return cmd_results_new(CMD_FAILURE, "hot_corner_size: Invalid size specified");
	}
	config->hot_corner_size = value;
	return cmd_results_new(CMD_SUCCESS, NULL);
}
