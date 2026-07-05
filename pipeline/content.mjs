// Hinglish kids content. Style tag keeps every AI image visually consistent.
export const STYLE =
  "cute 3d pixar style render, kids cartoon, big sparkly eyes, soft rounded shapes, vibrant pastel colors, smooth lighting, adorable, high quality";

export const RHYME = {
  id: "rhyme",
  title: "Nacho Nacho Hathi Raja | Colors Song",
  voice: "hi-IN-SwaraNeural",
  ttsOpts: { pitch: "+20Hz", rate: "+8%" },
  character: {
    key: "hathi",
    prompt: `happy baby elephant dancing, arms up, wearing tiny golden crown, ${STYLE}, isolated on pure white background, sticker`,
  },
  lines: [
    { text: "Hathi Raja aaya aaya, dhoom machao re!", prop: "drum", propPrompt: "colorful indian dhol drum" },
    { text: "Nacho nacho sab milke, taali bajao re!", prop: "hands", propPrompt: "cute cartoon clapping hands with sparkles" },
    { text: "Red red apple, laal laal apple!", prop: "apple", propPrompt: "shiny red apple with cute smiling face" },
    { text: "Yellow yellow kela, meetha meetha kela!", prop: "banana", propPrompt: "happy yellow banana with cute smiling face" },
    { text: "Green green pattey, jhoomo jhoomo re!", prop: "leaf", propPrompt: "cute green leaf character dancing" },
    { text: "Blue blue paani, chhap chhap paani!", prop: "water", propPrompt: "cute blue water drop character splashing" },
    { text: "Nacho nacho Hathi Raja, nacho nacho re!", prop: "drum" },
    { text: "Colors ki duniya mein, aao gaao re!", prop: "rainbow", propPrompt: "cute smiling rainbow with fluffy clouds" },
    { text: "Ek do teen chaar, colors hain hazaar!", prop: "stars", propPrompt: "colorful cute stars with happy faces" },
    { text: "Hathi Raja bola: bye bye, phir milenge yaar!", prop: "wave", propPrompt: "baby elephant waving goodbye with crown" },
  ],
};

export const STORY = {
  id: "story",
  title: "Chintu Hathi Aur Magic Rainbow | Moral Story",
  voice: "hi-IN-MadhurNeural",
  ttsOpts: { pitch: "+5Hz", rate: "-4%" },
  character: {
    key: "chintu",
    prompt: `adorable baby elephant with red scarf, ${STYLE}, isolated on pure white background, sticker`,
  },
  lines: [
    { text: "Ek jungle mein Chintu naam ka chhota hathi rehta tha.", scene: "s1", scenePrompt: "lush green magical jungle with sunlight, flowers" },
    { text: "Chintu bahut sad tha, kyunki uska koi friend nahi tha.", scene: "s2", scenePrompt: "sad baby elephant sitting alone under big tree, evening light" },
    { text: "Ek din baarish ke baad, sky mein magic rainbow aaya!", scene: "s3", scenePrompt: "giant glowing rainbow over jungle after rain, sparkles" },
    { text: "Rainbow bola: Chintu, smile karo, sabko hello bolo!", scene: "s4", scenePrompt: "baby elephant looking up at talking magical rainbow, amazed" },
    { text: "Chintu ne bunny ko bola hello, aur monkey ko bola hi!", scene: "s5", scenePrompt: "baby elephant greeting cute bunny and monkey, jungle" },
    { text: "Sab bole: wow Chintu, tum kitne friendly ho!", scene: "s6", scenePrompt: "happy jungle animals hugging baby elephant, celebration" },
    { text: "Ab Chintu ke bahut saare friends the, sab khush the!", scene: "s7", scenePrompt: "baby elephant playing with animal friends under rainbow" },
    { text: "Moral: Smile karo, hello bolo, friends banao!", scene: "s8", scenePrompt: "all cute animals waving together, sunset, rainbow, hearts" },
  ],
};
