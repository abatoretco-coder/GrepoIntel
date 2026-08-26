import test from "node:test";
import assert from "node:assert/strict";
import {sanitize} from "../dist/sanitize.js";

test("snapshot sanitizer removes credentials recursively",()=>{
  const cleaned=sanitize({name:"Abator",cookie:"no",nested:{csrfToken:"no",units:{sword:4}},cities:[{session_id:"no",wood:12}]});
  const raw=JSON.stringify(cleaned).toLowerCase();
  for(const word of ["cookie","csrf","token","session"]) assert.equal(raw.includes(word),false);
  assert.equal(cleaned.nested.units.sword,4);
});
