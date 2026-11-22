shader_type canvas_item;
// The realm's painted ground (RealmGround): TEXTURE is the material map, one texel per square
// (0 = none: the tiles underneath show, 1..n = a ground texture in `atlas`, 256 px each, side by side).
// Each pixel blends the 4 nearest squares' textures, with the square edges pushed about by value
// noise so a road's edge wobbles like trodden earth. One quad covers the whole realm: no screen seams.

uniform sampler2D atlas : filter_nearest, repeat_disable;
uniform int count = 1;            // textures in the atlas
uniform float tex_size = 256.0;
uniform float tile = 32.0;
uniform float wobble = 0.35;      // how far (in squares) the noise moves an edge
uniform float soft = 0.3;         // half-width of the blend between two squares (0..0.5 of a square)

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

vec4 tex_at(int m, vec2 px) {
	if (m <= 0 || m > count) return vec4(0.0);
	ivec2 t = ivec2(mod(px, tex_size));
	return texelFetch(atlas, t + ivec2((m - 1) * int(tex_size), 0), 0);
}

void fragment() {
	ivec2 cells = textureSize(TEXTURE, 0);
	vec2 px = floor(UV * vec2(cells) * tile);           // this game pixel
	vec2 n = vec2(noise(px / 23.0), noise(px / 23.0 + 17.3)) - 0.5;
	vec2 n2 = vec2(noise(px / 7.0 + 3.1), noise(px / 7.0 + 9.7)) - 0.5;
	vec2 q = px / tile + (n * 2.0 + n2 * 0.6) * wobble - 0.5;
	ivec2 b = ivec2(floor(q));
	vec2 f = smoothstep(vec2(0.5 - soft), vec2(0.5 + soft), fract(q));
	vec4 col = vec4(0.0);
	for (int j = 0; j < 2; j++) {
		for (int i = 0; i < 2; i++) {
			ivec2 c = clamp(b + ivec2(i, j), ivec2(0), cells - 1);
			int m = int(round(texelFetch(TEXTURE, c, 0).r * 255.0));
			float w = (i == 0 ? 1.0 - f.x : f.x) * (j == 0 ? 1.0 - f.y : f.y);
			col += tex_at(m, px) * w;
		}
	}
	COLOR = col;
}
