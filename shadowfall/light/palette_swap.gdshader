// The darkening world (B3): remaps world colours to the gloom stage's palette (GloomLut.image()).
// Put it on world tiles and backgrounds only (GloomLight.world_material); characters and the HUD
// never get it, so they always read. GLSL ES 3.0 only, so it runs in the web export (WebGL 2).
shader_type canvas_item;

uniform sampler2D lut : filter_nearest, repeat_disable;
uniform int stage = 0;

void fragment() {
	vec4 c = COLOR;  // texture colour times modulate (or the draw colour)
	if (stage > 0 && c.a > 0.0) {
		int best = 0;
		float bd = 1e9;
		for (int i = 0; i < 32; i++) {
			vec3 d = c.rgb - texelFetch(lut, ivec2(i, 0), 0).rgb;
			float dd = dot(d, d);
			if (dd < bd) {
				bd = dd;
				best = i;
			}
		}
		vec3 from = texelFetch(lut, ivec2(best, 0), 0).rgb;
		vec3 to = texelFetch(lut, ivec2(best, clamp(stage, 0, 3)), 0).rgb;
		c.rgb = clamp(c.rgb + to - from, 0.0, 1.0);
	}
	COLOR = c;
}
