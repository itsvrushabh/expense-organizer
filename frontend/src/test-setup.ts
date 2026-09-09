import { GlobalRegistrator } from "@happy-dom/global-registrator";

GlobalRegistrator.register();

// Mock dialog functions to avoid hanging interactive CLI prompts
window.confirm = () => true;
window.alert = () => {};
