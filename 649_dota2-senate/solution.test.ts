import { predictPartyVictory } from './solution';

describe('649. Dota2 Senate', () => {
  it('exports predictPartyVictory', () => {
    expect(predictPartyVictory).toBeInstanceOf(Function);
  });

  it('example 1: Radiant bans the only Dire senator', () => {
    expect(predictPartyVictory('RD')).toBe('Radiant');
  });

  it('example 2: Dire outnumbers Radiant', () => {
    expect(predictPartyVictory('RDD')).toBe('Dire');
  });
});
