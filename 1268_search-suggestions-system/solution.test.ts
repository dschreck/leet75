import { suggestedProducts } from './solution';

describe('1268. Search Suggestions System', () => {
  it('exports suggestedProducts', () => {
    expect(suggestedProducts).toBeInstanceOf(Function);
  });

  it('example 1: suggestions narrow as the word is typed', () => {
    expect(
      suggestedProducts(
        ['mobile', 'mouse', 'moneypot', 'monitor', 'mousepad'],
        'mouse',
      ),
    ).toEqual([
      ['mobile', 'moneypot', 'monitor'],
      ['mobile', 'moneypot', 'monitor'],
      ['mouse', 'mousepad'],
      ['mouse', 'mousepad'],
      ['mouse', 'mousepad'],
    ]);
  });

  it('example 2: the only product is always suggested', () => {
    expect(suggestedProducts(['havana'], 'havana')).toEqual([
      ['havana'],
      ['havana'],
      ['havana'],
      ['havana'],
      ['havana'],
      ['havana'],
    ]);
  });
});
