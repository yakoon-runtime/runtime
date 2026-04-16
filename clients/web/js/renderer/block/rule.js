import { registerBlock } from "./core.js";
import { createElement } from "../../dom.js";

registerBlock("rule", () => {
    return createElement("hr", "rule");
});