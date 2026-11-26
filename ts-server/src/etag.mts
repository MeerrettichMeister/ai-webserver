/**
 * ETags: a row's version is sent as `ETag: "<version>"`. Clients send it back in `If-Match` to
 * make a write conditional, or in `If-None-Match` to get `304 Not Modified` while it is current.
 */

/** The versions an `If-Match`/`If-None-Match` header names: any (`*`) or a set of them. */
export type ExpectedVersion = '*' | ReadonlySet<number>;

/** A version tag: `"3"`, or leniently the bare number `3`. Other tags never match. */
const VERSION_TAG = /^(?:"(\d+)"|(\d+))$/u;

export const etag = (version: number): string => `"${version}"`;

/**
 * The versions a header lists (comma separated).
 *
 * @param weak also accept weak tags (`W/"3"`), as for `If-None-Match`. `If-Match` uses the strong
 *   comparison, where a weak tag never matches (RFC 9110).
 */
export const parseETags = (header: string, weak: boolean): ExpectedVersion => {
  const tags = header.split(',').map((tag) => tag.trim());
  if (tags.includes('*')) {
    return '*';
  }
  const versions = new Set<number>();
  for (const tag of tags) {
    const match = VERSION_TAG.exec(weak ? tag.replace(/^W\//u, '') : tag);
    if (match !== null) {
      versions.add(Number(match[1] ?? match[2]));
    }
  }
  return versions;
};

export const matches = (expected: ExpectedVersion, version: number): boolean =>
  expected === '*' || expected.has(version);
