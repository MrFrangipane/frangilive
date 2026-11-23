#define _POSIX_C_SOURCE 200809L
#include <jack/jack.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define MAX_PORTS 128

typedef struct {
    jack_client_t *client;
    unsigned inputs, outputs, fade_samples;
    jack_port_t *in[MAX_PORTS], *out[MAX_PORTS];
    const jack_default_audio_sample_t *in_buffer[MAX_PORTS];
    _Atomic unsigned char target[MAX_PORTS * MAX_PORTS];
    float gain[MAX_PORTS * MAX_PORTS];
} matrix_t;

static int process(jack_nframes_t nframes, void *arg)
{
    matrix_t *m = arg;
    unsigned i, o;
    jack_nframes_t n;
    float step = 1.0f / m->fade_samples;
    for (i = 0; i < m->inputs; ++i)
        m->in_buffer[i] = jack_port_get_buffer(m->in[i], nframes);
    for (o = 0; o < m->outputs; ++o) {
        jack_default_audio_sample_t *out = jack_port_get_buffer(m->out[o], nframes);
        memset(out, 0, nframes * sizeof(*out));
        for (i = 0; i < m->inputs; ++i) {
            unsigned index = o * m->inputs + i;
            float gain = m->gain[index];
            float target = atomic_load_explicit(&m->target[index], memory_order_relaxed) ? 1.0f : 0.0f;
            if (gain == 0.0f && target == 0.0f) continue;
            for (n = 0; n < nframes; ++n) {
                if (gain < target) gain = fminf(target, gain + step);
                else if (gain > target) gain = fmaxf(target, gain - step);
                out[n] += m->in_buffer[i][n] * gain;
            }
            m->gain[index] = gain;
        }
    }
    return 0;
}

static int parse_uint(const char *s, unsigned *out, unsigned max)
{
    char *end;
    unsigned long value;
    if (!*s || *s == '-' || *s == '+') return 0;
    value = strtoul(s, &end, 10);
    if (*end || value > max) return 0;
    *out = (unsigned)value;
    return 1;
}

int main(int argc, char **argv)
{
    matrix_t *m = calloc(1, sizeof(*m));
    const char *name = "jack-matrix";
    unsigned fade_ms = 5, i;
    char port_name[32], line[256];
    int status = 1;
    if (!m) return 1;
    for (i = 1; i < (unsigned)argc; ++i) {
        const char *option = argv[i];
        if (++i >= (unsigned)argc) goto usage;
        if (!strcmp(option, "--inputs")) {
            if (!parse_uint(argv[i], &m->inputs, MAX_PORTS) || !m->inputs) goto usage;
        } else if (!strcmp(option, "--outputs")) {
            if (!parse_uint(argv[i], &m->outputs, MAX_PORTS) || !m->outputs) goto usage;
        } else if (!strcmp(option, "--fade-ms")) {
            if (!parse_uint(argv[i], &fade_ms, 10000)) goto usage;
        } else if (!strcmp(option, "--name")) name = argv[i];
        else goto usage;
    }
    if (!m->inputs || !m->outputs) goto usage;
    for (i = 0; i < m->inputs * m->outputs; ++i) {
        atomic_init(&m->target[i], 0);
        if (!atomic_is_lock_free(&m->target[i])) {
            fprintf(stderr, "atomic route state is not lock-free\n");
            goto done;
        }
    }
    m->client = jack_client_open(name, JackNoStartServer | JackUseExactName, NULL);
    if (!m->client) { fprintf(stderr, "cannot open JACK client\n"); goto done; }
    m->fade_samples = (unsigned)((uint64_t)jack_get_sample_rate(m->client) * fade_ms / 1000);
    if (!m->fade_samples) m->fade_samples = 1;
    for (i = 0; i < m->inputs; ++i) {
        snprintf(port_name, sizeof(port_name), "in_%u", i);
        m->in[i] = jack_port_register(m->client, port_name, JACK_DEFAULT_AUDIO_TYPE, JackPortIsInput, 0);
        if (!m->in[i]) goto jack_error;
    }
    for (i = 0; i < m->outputs; ++i) {
        snprintf(port_name, sizeof(port_name), "out_%u", i);
        m->out[i] = jack_port_register(m->client, port_name, JACK_DEFAULT_AUDIO_TYPE, JackPortIsOutput, 0);
        if (!m->out[i]) goto jack_error;
    }
    if (jack_set_process_callback(m->client, process, m) || jack_activate(m->client)) goto jack_error;
    while (fgets(line, sizeof(line), stdin)) {
        char *command, *a, *b, *c, *extra, *save;
        unsigned input, output, enabled;
        if (!strchr(line, '\n') && !feof(stdin)) {
            int ch;
            while ((ch = getchar()) != '\n' && ch != EOF) {}
            puts("ERR line too long"); fflush(stdout); continue;
        }
        command = strtok_r(line, " \t\r\n", &save);
        a = strtok_r(NULL, " \t\r\n", &save);
        b = strtok_r(NULL, " \t\r\n", &save);
        c = strtok_r(NULL, " \t\r\n", &save);
        extra = strtok_r(NULL, " \t\r\n", &save);
        if (command && !strcmp(command, "QUIT") && !a) {
            puts("OK"); fflush(stdout); break;
        }
        if (command && !strcmp(command, "SET") && a && b && c && !extra &&
            parse_uint(a, &input, m->inputs - 1) && parse_uint(b, &output, m->outputs - 1) &&
            parse_uint(c, &enabled, 1)) {
            atomic_store_explicit(&m->target[output * m->inputs + input], (unsigned char)enabled, memory_order_relaxed);
            puts("OK");
        } else puts("ERR invalid command");
        fflush(stdout);
    }
    status = 0;
    jack_deactivate(m->client);
    goto done;
jack_error:
    fprintf(stderr, "cannot register JACK ports or activate client\n");
    goto done;
usage:
    fprintf(stderr, "usage: jack-matrix --inputs N --outputs N [--name NAME] [--fade-ms MS]\n");
done:
    if (m->client) jack_client_close(m->client);
    free(m);
    return status;
}
