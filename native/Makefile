CC ?= cc
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Wpedantic
JACK_CFLAGS := $(shell pkg-config --cflags jack)
JACK_LIBS := $(shell pkg-config --libs jack)

jack-matrix: matrix.c
	$(CC) $(CFLAGS) $(JACK_CFLAGS) -o $@ $< $(JACK_LIBS) -lm

test-matrix: test_matrix.c matrix.c
	$(CC) $(CFLAGS) $(JACK_CFLAGS) -o $@ test_matrix.c $(JACK_LIBS) -lm

test: test-matrix
	./test-matrix

clean:
	rm -f jack-matrix test-matrix

.PHONY: clean test
