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

int main(void)
{
    matrix_t *m = calloc(1, sizeof(*m));
    float input0[] = {1, 1, 1, 1}, input1[] = {2, 2, 2, 2}, output[4];
    unsigned value;
    assert(m);
    m->inputs = 2; m->outputs = 1; m->fade_samples = 4;
    m->in[0] = (jack_port_t *)input0; m->in[1] = (jack_port_t *)input1;
    m->out[0] = (jack_port_t *)output;
    atomic_init(&m->target[0], 0); atomic_init(&m->target[1], 0);
    process(4, m); check(output[0], 0); check(output[3], 0);
    atomic_store(&m->target[0], 1);
    process(2, m); check(output[0], 0.25f); check(output[1], 0.5f);
    atomic_store(&m->target[0], 0);
    process(2, m); check(output[0], 0.25f); check(output[1], 0);
    atomic_store(&m->target[0], 1); atomic_store(&m->target[1], 1);
    process(4, m); check(output[0], 0.75f); check(output[3], 3);
    process(4, m); check(output[0], 3); check(output[3], 3);
    assert(parse_uint("127", &value, 127) && value == 127);
    assert(!parse_uint("-1", &value, 127));
    assert(!parse_uint("128", &value, 127));
    assert(!parse_uint("1x", &value, 127));
    free(m);
    puts("matrix tests passed");
    return 0;
}
