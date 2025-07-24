export class AppUtils {

  /**
	 * Custom async setTimeOut for waiting end of exe
	 */
	static async timeOut(ms, callback: any = null) {
		return new Promise<void>(resolve =>
			setTimeout(() => {
				if (callback) {
					callback();
				}
				resolve();
			}, ms)
		);
	}
}
