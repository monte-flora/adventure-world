// Painted art (realm props, cave paintings) under the gloom: GloomLight.painted_material.
// GLSL ES 3.0 only, so it runs in the web export.
shader_type canvas_item;
#include "res://light/painted_gloom.gdshaderinc"

uniform int stage = 0;

void fragment() {
	COLOR.rgb = gloom_grade(COLOR.rgb, stage);
}
