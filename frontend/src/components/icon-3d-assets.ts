// One bookmark asset pair shared by the Reader's Save action and Saved tab.
export const BOOKMARK_3D = {
  base: require("../../assets/images/act-bookmark-base.png"),
  active: require("../../assets/images/act-bookmark-active.png"),
} as const;

export const TAB_ART_3D = {
  discover: { base: require("../../assets/images/nav-home-base.png"), active: require("../../assets/images/nav-home-active.png") },
  explore: { base: require("../../assets/images/nav-topics-base.png"), active: require("../../assets/images/nav-topics-active.png") },
  bookmarks: BOOKMARK_3D,
  profile: { base: require("../../assets/images/nav-profile-base.png"), active: require("../../assets/images/nav-profile-active.png") },
} as const;