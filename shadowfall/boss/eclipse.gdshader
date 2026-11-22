shader_type canvas_item;
// The Eclipse: the throne room goes black but for your lantern's circle, cut in 3 hard rings
// (docs/teen/art/README.md: 100/72/45% of the radius, hero lantern 130 px).

uniform vec2 hero_px = vec2(480.0, 270.0);
uniform vec2 room_px = vec2(960.0, 540.0);
uniform float radius = 130.0;
uniform float strength = 0.96;
uniform vec4 ink : source_color = vec4(0.05, 0.04, 0.08, 1.0);

void fragment() {
	float d = distance(UV * room_px, hero_px) / radius;
	float a = d > 1.0 ? strength : (d > 0.72 ? 0.6 : (d > 0.45 ? 0.3 : 0.0));
	COLOR = vec4(ink.rgb, a);
}
