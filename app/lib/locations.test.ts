import assert from "node:assert/strict";
import test from "node:test";
import { getCitiesByCountry, getSelectableCity } from "./locations";

test("getSelectableCity keeps a registered city for the country", () => {
  const [firstCity, secondCity] = getCitiesByCountry("KR");

  assert.equal(getSelectableCity(secondCity.city, "KR"), secondCity.city);
  assert.notEqual(getSelectableCity(secondCity.city, "KR"), firstCity.city);
});

test("getSelectableCity falls back to the first city when stored city is outside the country list", () => {
  const [firstJapaneseCity] = getCitiesByCountry("JP");

  assert.equal(getSelectableCity("Busan", "JP"), firstJapaneseCity.city);
  assert.equal(getSelectableCity("", "JP"), firstJapaneseCity.city);
});
