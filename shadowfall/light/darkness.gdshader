// The dark over the world (B3): ink0 at `darkness` alpha, cut by light pools in 3 hard rings
// (100/72/45% of the radius: 2/3, 1/3, 0 of the dark). Overlapping pools take the lowest dark.
// Same rule as GloomLight.darkness_at(). GLSL ES 3.0 only, so it runs in the web export.
shader_type canvas_item;

const int MAX_POOLS = 16;
uniform vec4 ink : source_color = vec4(0.043, 0.039, 0.071, 1.0);
uniform float darkness = 0.0;
uniform vec2 rect_size = vec2(960.0, 540.0);
uniform int count = 0;
uniform vec2 pools[MAX_POOLS];
uniform float radii[MAX_POOLS];

void fragment() {
	vec2 p = UV * rect_size;
	float a = darkness;
	for (int i = 0; i < MAX_POOLS; i++) {
		if (i >= count) {
			break;
		}
		float d = distance(p, pools[i]) / max(radii[i], 0.001);
		float k = d < 0.45 ? 0.0 : (d < 0.72 ? 1.0 / 3.0 : (d < 1.0 ? 2.0 / 3.0 : 1.0));
		a = min(a, darkness * k);
	}
	COLOR = vec4(ink.rgb, a);
}
