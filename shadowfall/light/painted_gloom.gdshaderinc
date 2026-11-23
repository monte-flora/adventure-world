// The darkening world for painted art (G2): Gemini paintings are not in Shadowfall 32, so the palette
// swap would band them. This grade does the same look smoothly: per gloom stage, drain the colour,
// pull it toward violet and darken it, about as much as palette_swap's ramp steps do on average.
// Keep in step with PaintedGloom (light/painted_gloom.gd), which tests use on the CPU.
const float GLOOM_SAT[4] = float[4](1.0, 0.8, 0.6, 0.4);
const float GLOOM_SHIFT[4] = float[4](0.0, 0.12, 0.24, 0.36);
const float GLOOM_VALUE[4] = float[4](1.0, 0.8, 0.64, 0.52);
const vec3 GLOOM_VIOLET = vec3(0.82, 0.74, 1.3);

vec3 gloom_grade(vec3 c, int stage) {
	int s = clamp(stage, 0, 3);
	float l = dot(c, vec3(0.299, 0.587, 0.114));
	c = mix(vec3(l), c, GLOOM_SAT[s]);
	c = mix(c, l * GLOOM_VIOLET, GLOOM_SHIFT[s]);
	return clamp(c * GLOOM_VALUE[s], 0.0, 1.0);
}
