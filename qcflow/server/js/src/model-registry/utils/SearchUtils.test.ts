/**
 * NOTE: this code file was automatically migrated to TypeScript using ts-migrate and
 * may contain multiple `any` type annotations and `@ts-expect-error` directives.
 * If possible, please improve types while making changes to this file. If the type
 * annotations are already looking good, please remove this comment.
 */

import { getModelNameFilter, getCombinedSearchFilter, constructSearchInputFromURLState } from './SearchUtils';

describe('getModelNameFilter', () => {
  it('should construct name filter correctly', () => {
    expect(getModelNameFilter('abc')).toBe("name ilike '%abc%'");
  });
});

describe('getCombinedSearchFilter', () => {
  it('should return filter string correctly with plain name strings', () => {
    expect(getCombinedSearchFilter({ query: 'xyz' })).toBe("name ilike '%xyz%'");
  });

  it('should return filter string correctly with QCFlow Search Syntax string with tags.', () => {
    expect(getCombinedSearchFilter({ query: "tags.k = 'v'" })).toBe("tags.k = 'v'");
  });

  it('should return filter string correctly with QCFlow Search Syntax string with tags. and name', () => {
    expect(getCombinedSearchFilter({ query: "name ilike '%abc%' AND tags.k = 'v'" })).toBe(
      "name ilike '%abc%' AND tags.k = 'v'",
    );
  });
});

describe('constructSearchInputFromURLState', () => {
  it('should construct searchInput correctly from URLState with nameSearchInput', () => {
    expect(constructSearchInputFromURLState({ nameSearchInput: 'xyz' })).toBe('xyz');
  });

  it('should construct searchInput correctly from URLState with tagSearchInput', () => {
    expect(constructSearchInputFromURLState({ tagSearchInput: "tags.k = 'v'" })).toBe("tags.k = 'v'");
  });

  it('should construct searchInput correctly from URLState with nameSearchInput and tagSearchInput', () => {
    expect(
      constructSearchInputFromURLState({
        nameSearchInput: 'xyz',
        tagSearchInput: "tags.k = 'v'",
      }),
    ).toBe("name ilike '%xyz%' AND tags.k = 'v'");
  });

  it('should construct searchInput correctly from URLState with searchInput', () => {
    expect(
      constructSearchInputFromURLState({
        searchInput: 'name ilike "%xyz%" AND tags.k = "v"',
      }),
    ).toBe('name ilike "%xyz%" AND tags.k = "v"');
  });
});
