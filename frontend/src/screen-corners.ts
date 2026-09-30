// PAUSE — raggio degli angoli dello schermo del dispositivo (in punti), per
// far correre la cornice luminosa esattamente lungo il vetro: sui telefoni con
// schermo stondato (iPhone con notch/Dynamic Island, Galaxy, Pixel…) la linea
// segue la curva; su schermi squadrati (iPhone SE, tablet, web) resta dritta.
// Nessuna API pubblica espone il valore in Expo Go: si riconosce il modello
// (expo-device) e si usa il raggio noto; in mancanza, una stima prudente dalle
// barre di sistema (schermo "a tutto vetro" → angoli stondati).
import { Platform } from "react-native";
import * as Device from "expo-device";
import { useSafeAreaInsets } from "react-native-safe-area-context";

// iPhone: identificatore hardware → raggio del vetro (pt). Fonte: misure note
// dei modelli (display corner radius). I modelli con Touch ID hanno angoli squadrati.
const IPHONE_RADIUS: Record<string, number> = {
  "iPhone10,3": 39, "iPhone10,6": 39,                     // X
  "iPhone11,2": 39, "iPhone11,4": 39, "iPhone11,6": 39,    // XS / XS Max
  "iPhone11,8": 41.5,                                      // XR
  "iPhone12,1": 41.5, "iPhone12,3": 39, "iPhone12,5": 39,  // 11 / 11 Pro / 11 Pro Max
  "iPhone13,1": 44, "iPhone13,2": 47.33, "iPhone13,3": 47.33, "iPhone13,4": 53.33, // 12 mini / 12 / 12 Pro / 12 Pro Max
  "iPhone14,4": 44, "iPhone14,5": 47.33, "iPhone14,2": 47.33, "iPhone14,3": 53.33, // 13 mini / 13 / 13 Pro / 13 Pro Max
  "iPhone14,7": 47.33, "iPhone14,8": 53.33, "iPhone15,2": 55, "iPhone15,3": 55,    // 14 / 14 Plus / 14 Pro / 14 Pro Max
  "iPhone15,4": 55, "iPhone15,5": 55, "iPhone16,1": 55, "iPhone16,2": 55,          // 15 / 15 Plus / 15 Pro / 15 Pro Max
  "iPhone17,3": 55, "iPhone17,4": 55, "iPhone17,1": 62, "iPhone17,2": 62,          // 16 / 16 Plus / 16 Pro / 16 Pro Max
  "iPhone17,5": 55,                                                                // 16e
  "iPhone18,3": 62, "iPhone18,1": 62, "iPhone18,2": 62, "iPhone18,4": 62,          // 17 / 17 Pro / 17 Pro Max / Air
};

// Android: famiglie di modelli con raggio noto (dp). Le serie "Ultra"/"Note"
// hanno angoli più stretti; le altre Galaxy S/Z e i Pixel recenti più ampi.
function androidRadius(model: string, brand: string): number | null {
  const m = model.toLowerCase(), b = brand.toLowerCase();
  if (b.includes("samsung") || m.startsWith("sm-") || m.includes("galaxy")) {
    if (m.includes("ultra") || m.includes("note") || /sm-s9[0-9]8/.test(m) || /sm-n9/.test(m)) return 22;
    if (m.includes("fold") || m.includes("flip") || /sm-f9/.test(m)) return 30;
    if (m.includes("galaxy s") || /sm-s9[0-9][0-9]/.test(m) || /sm-g9/.test(m)) return 38;
    if (m.includes("galaxy a") || /sm-a[0-9]/.test(m)) return 32;
    return 34;
  }
  if (b.includes("google") || m.includes("pixel")) return m.includes("fold") ? 32 : 40;
  if (b.includes("oneplus") || b.includes("oppo") || b.includes("realme")) return 36;
  if (b.includes("xiaomi") || b.includes("redmi") || b.includes("poco")) return 32;
  if (b.includes("motorola")) return 34;
  if (b.includes("nothing")) return 42;
  if (b.includes("huawei") || b.includes("honor")) return 34;
  return null;
}

export function useScreenCornerRadius(): number {
  const insets = useSafeAreaInsets();
  let radius = 0;
  if (Platform.OS === "web") {
    // Anteprima nel browser: nessun vetro stondato, si tiene il raggio "di disegno".
    radius = 28;
  } else if (Device.deviceType === Device.DeviceType.TABLET) {
    radius = Platform.OS === "ios" && insets.top >= 20 && insets.bottom > 0 ? 18 : 0;
  } else if (Platform.OS === "ios") {
    const known = Device.modelId ? IPHONE_RADIUS[Device.modelId] : undefined;
    // Sconosciuto (modello futuro): con Dynamic Island/notch gli angoli sono stondati.
    radius = known ?? (insets.top >= 44 ? 55 : 0);
  } else {
    const known = androidRadius(Device.modelName ?? "", Device.brand ?? Device.manufacturer ?? "");
    // Sconosciuto: schermo "a tutto vetro" (barra di stato alta, gesture) → stondato.
    radius = known ?? (insets.top >= 24 ? 32 : 0);
  }
  return radius;
}
