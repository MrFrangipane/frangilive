#define main matrix_main
#include "matrix.c"
#undef main
#include <assert.h>

void *jack_port_get_buffer(jack_port_t *port, jack_nframes_t nframes)
{
    (void)nframes;
    return (void *)port;
}

static void check(float actual, float expected)
{
    assert(fabsf(actual - expected) < 0.0001f);
}

static int command_matrix(matrix_t *m, char *line)
{
    char *save;
    assert(!strcmp(strtok_r(line, " \t\r\n", &save), "MATRIX"));
    return parse_matrix(m, &save);
}

int main(void)
{
    matrix_t *m = calloc(1, sizeof(*m));
    float input0[] = {1, 1, 1, 1}, input1[] = {2, 2, 2, 2}, output[4];
    char both[] = "MATRIX 0,0 1,0", bad[] = "MATRIX 0,0 2,0", empty[] = "MATRIX";
    unsigned value;
    assert(m);
    m->inputs = 2; m->outputs = 1; m->fade_samples = 4;
    m->in[0] = (jack_port_t *)input0; m->in[1] = (jack_port_t *)input1;
    m->out[0] = (jack_port_t *)output;
    m->writer = 0; m->reader = 1; atomic_init(&m->middle, 2);
    process(4, m); check(output[0], 0); check(output[3], 0);
    m->control[0] = 1; publish(m);
    process(2, m); check(output[0], 0.25f); check(output[1], 0.5f);
    m->control[0] = 0; publish(m);
    process(2, m); check(output[0], 0.25f); check(output[1], 0);
    assert(command_matrix(m, both));
    assert(!command_matrix(m, bad));
    process(4, m); check(output[0], 0.75f); check(output[3], 3);
    process(4, m); check(output[0], 3); check(output[3], 3);
    assert(command_matrix(m, empty));
    process(4, m); check(output[0], 2.25f); check(output[3], 0);
    m->control[0] = 1; publish(m);
    m->control[0] = 0; m->control[1] = 1; publish(m);
    process(4, m); check(output[0], 0.5f); check(output[3], 2);
    assert(parse_uint("127", &value, 127) && value == 127);
    assert(!parse_uint("-1", &value, 127));
    assert(!parse_uint("128", &value, 127));
    assert(!parse_uint("1x", &value, 127));
    free(m);
    puts("matrix tests passed");
    return 0;
}
