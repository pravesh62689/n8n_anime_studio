// SEO metadata engine for Hinglish kids' videos — optimized for YouTube search + recommendations.
// Peak IST times for Indian kids' content: 8AM (before school), 1PM (lunch), 6PM (evening play).

const PEAK_HOURS_IST = [8, 13, 18]; // 3 uploads/day at peak viewing times

// High-traffic keywords for Indian kids' content (researched from Infobells/ChuChu TV/Cocomelon patterns)
const BASE_TAGS = [
  "hindi rhymes for kids", "hindi rhymes", "nursery rhymes hindi", "kids songs hindi",
  "baby songs", "hindi cartoon", "kids video", "balgeet", "hindi poem for kids",
  "rhymes for children", "toddler songs", "hindi kahani", "kids learning video",
  "cartoon for kids in hindi", "children songs", "preschool learning",
];

export function buildMetadata({ type, title, topic, keywords = [] }) {
  const isRhyme = type === "rhyme";
  const seoTitle = isRhyme
    ? `${title} | Hindi Rhymes for Kids | Nursery Rhymes | Kids Songs`
    : `${title} | Hindi Kahani for Kids | Moral Stories | Kids Cartoon`;

  const description = [
    isRhyme
      ? `${title} - A fun sing-along ${topic} song for kids! Watch, sing and dance with us!`
      : `${title} - A beautiful animated story with a moral for kids! ${topic}`,
    "",
    isRhyme
      ? "Is video mein bacche seekhenge naye words, colors aur numbers - gaane ke saath! Perfect for toddlers, preschoolers and young children."
      : "Yeh kahani bacchon ko achhi seekh deti hai. Perfect for bedtime stories and moral learning!",
    "",
    "SUBSCRIBE for new videos every day! Naye videos ke liye subscribe karein!",
    "",
    `#HindiRhymes #KidsSongs #${title.replace(/[^a-zA-Z0-9]/g, "")} #NurseryRhymes #HindiKahani #KidsVideo #Balgeet #CartoonForKids`,
  ].join("\n");

  return {
    title: seoTitle.slice(0, 100),
    description: description.slice(0, 5000),
    tags: [...new Set([...keywords, ...BASE_TAGS])].slice(0, 30),
    categoryId: "24", // Entertainment (kids' channels use 24 or 27/Education)
    defaultLanguage: "hi",
    madeForKids: true,
  };
}

// Next N peak publish times (IST = UTC+5:30), starting from tomorrow morning.
export function nextPeakTimes(count) {
  const times = [];
  const now = new Date();
  for (let day = 1; times.length < count; day++) {
    for (const hour of PEAK_HOURS_IST) {
      if (times.length >= count) break;
      // hour IST -> UTC: subtract 5h30m
      const d = new Date(Date.UTC(
        now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + day,
        hour - 6, 30, 0, 0,
      ));
      if (d > now) times.push(d.toISOString());
    }
  }
  return times;
}
